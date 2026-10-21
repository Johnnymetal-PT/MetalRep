# -*- coding: utf-8 -*-
"""Recuperação dos documentos de produto que ficaram presos a variantes mortas.

A causa está corrigida em `_preservar_documentos_de_variante` (commit 6cee129), mas
essa correção só fecha a torneira: os 5697 documentos já acumulados em produção
continuam presos a 1790 variantes que já não existem, invisíveis no site, no Odoo e
nos orçamentos.

Porque é que isto é um modelo no servidor e não um script por API
================================================================
Não é escolha de estilo. `ir.attachment._check_access` valida o acesso ao registo
apontado por `res_model`/`res_id`; quando esse registo não existe,
`_inaccessible_comodel_records` devolve-o como proibido e a leitura rebenta com
AccessError. Um script externo por JSON-RPC nem sequer consegue ler o **nome** dos
ficheiros que quer recuperar. Só `sudo()` passa — e `sudo()` só existe dentro do
servidor.

As regras de prudência, e de onde vêm
=====================================
Vêm da resposta da Ana Valente de 18/09: *"existem vários ficheiros que, entretanto,
atualizei e substitui na plataforma, ao repor como sugere essa versão irá ser
perdida"* e *"é prudente ter um certo cuidado com a reposição para não causar dano no
que está feito atualmente, para que não seja necessário verificar novamente artigo a
artigo"*.

Traduzidas em código:

1. **Nada é apagado.** Não há uma única chamada a `unlink` sobre `product.document`
   em lado nenhum deste ficheiro — o que se apaga são as linhas do próprio censo,
   quando se volta a analisar.
2. **Nada é substituído.** Religar um órfão acrescenta um documento ao artigo, nunca
   escreve por cima de outro. O risco real não é perder a versão nova da Ana — é a
   versão velha reaparecer ao lado dela e alguém enviar a errada ao cliente. Por isso
   qualquer órfão que cheire a cópia antiga de um ficheiro já colocado fica de fora.
3. **Nada aparece sem se querer.** O documento recuperado entra escondido: fora da
   página de produto e fora dos orçamentos. Recuperar devolve o acesso pelo Odoo, não
   muda o que o cliente vê.
4. **Nada é escrito sem uma pessoa ter dito que sim**, linha a linha, e a verificação
   é repetida no momento da escrita — o censo pode ter dias.

O sinal que decide é o conteúdo, não a origem nem o nome
=======================================================
A primeira versão comparava o `gdrive_file_id`, o identificador do ficheiro no
Google Drive. Contra os dados reais apanhou **zero** casos em 5904 — e não por o
campo estar vazio, que 94% dos órfãos o têm preenchido. O mesmo ficheiro foi
carregado para o Drive várias vezes e recebeu um identificador novo de cada vez: a
identidade da origem mudou, o conteúdo não.

O `checksum` do `ir.attachment`, que é o resumo do conteúdo byte a byte, apanhou
**5388 dos 5904**. Nove em cada dez órfãos são cópias exatas de ficheiros que já
estão colocados e acessíveis: são redundantes, e podem sair de circulação sem
perder nada. É esta a comparação que decide, e é uma igualdade de conteúdo, não uma
heurística sobre nomes.

Sobra o que interessa: 516 registos sem gémeo vivo, que são apenas **127 ficheiros
distintos** — os únicos que se perdem mesmo se alguém apagar isto tudo. Nenhum
deles é recuperável pelo nome: ou não tem referência reconhecível, ou tem uma que
corresponde a vários artigos, por causa dos artigos duplicados nas importações. A
correspondência por nome acerta onde não é preciso e falha onde era, e por isso
deixou de ser o centro deste módulo: o que o censo faz de útil é **separar o
redundante do único** e entregar a lista dos únicos a quem conhece as referências.
"""

import logging
import re
from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Prefixos que a importação do Drive põe no nome ("FICHA TECNICA - xpto.pdf").
# Retirá-los antes de procurar a referência evita que as palavras do tipo entrem
# na comparação.
TIPOS_DRIVE = ("3D", "FICHA TECNICA", "CERTIFICADO CONFORMIDADE")

# Uma referência com 2 ou 3 caracteres aparece por acidente em quase qualquer nome de
# ficheiro e produziria ligações erradas. Abaixo disto não se arrisca.
MIN_REF = 4

ESTADOS = [
    ("duplicado_conteudo", "Redundante — o ficheiro já está colocado"),
    ("ligavel", "Recuperável"),
    ("duplicado_nome", "Já existe (mesmo nome no artigo)"),
    ("versao_antiga", "Possível versão antiga"),
    ("ambiguo", "Referência em vários artigos"),
    ("sem_referencia", "Sem referência no nome"),
]


def normalizar(texto):
    """Reduz a comparação ao que sobrevive a mudanças de formatação.

    'ess 2040 b manual.pdf' e 'ESS-2040-B' têm de encontrar-se: os separadores são
    ruído dos dois lados.
    """
    return re.sub(r"[^A-Z0-9]", "", (texto or "").upper())


def sem_prefixo_tipo(nome):
    """Tira o 'FICHA TECNICA - ' da frente, se lá estiver."""
    for tipo in TIPOS_DRIVE:
        if (nome or "").upper().startswith(tipo + " - "):
            return nome[len(tipo) + 3:], tipo
    return nome or "", ""


class PgDocumentoOrfaoCenso(models.Model):
    _name = "pg.documento.orfao.censo"
    _description = "Censo de documentos de produto orfaos"
    _order = "id desc"

    name = fields.Char(required=True, default=lambda self: fields.Datetime.now().strftime("Censo %d/%m/%Y %H:%M"))
    data = fields.Datetime(default=fields.Datetime.now, readonly=True)
    state = fields.Selection(
        [("rascunho", "Por analisar"), ("analisado", "Analisado"), ("aplicado", "Aplicado")],
        default="rascunho", readonly=True,
    )
    linha_ids = fields.One2many("pg.documento.orfao.linha", "censo_id")

    total_orfaos = fields.Integer(readonly=True)
    n_ligavel = fields.Integer("Recuperáveis", readonly=True)
    n_duplicado_conteudo = fields.Integer("Redundantes", readonly=True)
    n_duplicado_nome = fields.Integer("Já existem (nome)", readonly=True)
    n_versao_antiga = fields.Integer("Possíveis versões antigas", readonly=True)
    n_ambiguo = fields.Integer("Ambíguos", readonly=True)
    n_sem_referencia = fields.Integer("Sem referência", readonly=True)
    n_aplicados = fields.Integer("Documentos religados", readonly=True)
    n_unicos_registos = fields.Integer(
        "Registos sem gémeo", readonly=True,
        help="Órfãos cujo conteúdo não existe em mais lado nenhum. São estes, e só "
             "estes, que se perdem de facto se alguém apagar os órfãos.",
    )
    n_unicos_ficheiros = fields.Integer(
        "Ficheiros distintos sem gémeo", readonly=True,
        help="Os registos acima contados por conteúdo. As importações repetidas "
             "deixaram o mesmo ficheiro várias vezes, por isso este número é muito "
             "menor — e é o que interessa levar a quem conhece as referências.",
    )

    imagens_sem_produto = fields.Integer(
        "Imagens sem produto", readonly=True,
        help="A Ana perguntou se as imagens terão o mesmo problema. Têm um mecanismo "
             "diferente: product.image liga-se por many2one com ondelete='cascade', "
             "portanto ao apagar a variante a imagem é apagada, não fica órfã. Este "
             "número existe para responder com um facto em vez de com uma dedução.",
    )

    # ------------------------------------------------------------------ censo

    def action_analisar(self):
        for censo in self:
            censo._analisar(censo._documentos_orfaos())
        return True

    def _documentos_orfaos(self):
        """Documentos cujo `res_id` aponta para um registo que já não existe.

        Nao e `res_id = 0`: as variantes foram destruidas, e os documentos ficaram a
        apontar para ids concretos que deixaram de ter registo por tras.
        """
        Doc = self.env["product.document"].sudo().with_context(active_test=False)
        docs = Doc.search([("res_model", "in", ("product.product", "product.template"))])

        por_modelo = defaultdict(set)
        for doc in docs:
            if doc.res_id:
                por_modelo[doc.res_model].add(doc.res_id)
        vivos = {
            modelo: set(self.env[modelo].sudo().with_context(active_test=False).browse(sorted(ids)).exists().ids)
            for modelo, ids in por_modelo.items()
        }
        return docs.filtered(lambda d: not d.res_id or d.res_id not in vivos.get(d.res_model, ()))

    def _analisar(self, orfaos):
        """Classifica cada órfão. Não escreve nada em `product.document`."""
        self.ensure_one()
        self.linha_ids.unlink()

        indice_tmpl, indice_variante = self._indice_referencias()
        refs_ordenadas = sorted(indice_tmpl, key=len, reverse=True)
        checksums_vivos, docs_por_artigo = self._mapa_documentos_vivos(orfaos)

        linhas = []
        for doc in orfaos:
            linhas.append(self._classificar(
                doc, indice_tmpl, indice_variante, refs_ordenadas,
                checksums_vivos, docs_por_artigo,
            ))
        self.env["pg.documento.orfao.linha"].create([dict(l, censo_id=self.id) for l in linhas])

        contagens = defaultdict(int)
        for linha in linhas:
            contagens[linha["estado"]] += 1
        unicos = [l for l in linhas if l.get("unico")]
        self.write({
            "state": "analisado",
            "total_orfaos": len(linhas),
            "n_ligavel": contagens["ligavel"],
            "n_duplicado_conteudo": contagens["duplicado_conteudo"],
            "n_duplicado_nome": contagens["duplicado_nome"],
            "n_versao_antiga": contagens["versao_antiga"],
            "n_ambiguo": contagens["ambiguo"],
            "n_sem_referencia": contagens["sem_referencia"],
            "imagens_sem_produto": self._contar_imagens_sem_produto(),
            "n_unicos_registos": len(unicos),
            "n_unicos_ficheiros": len({l["checksum"] for l in unicos if l["checksum"]}),
        })
        _logger.info(
            "pg_product_update: censo de orfaos %s — %s documentos, %s redundantes, "
            "%s sem gemeo (%s ficheiros distintos).",
            self.id, len(linhas), contagens["duplicado_conteudo"], len(unicos),
            self.n_unicos_ficheiros,
        )
        return True

    def _indice_referencias(self):
        """referência normalizada -> ids de artigo, e -> id da variante viva."""
        Tmpl = self.env["product.template"].sudo().with_context(active_test=False)
        Prod = self.env["product.product"].sudo().with_context(active_test=False)

        indice_tmpl = defaultdict(set)
        for artigo in Tmpl.search_read([("default_code", "!=", False)], ["default_code"]):
            ref = normalizar(artigo["default_code"])
            if len(ref) >= MIN_REF:
                indice_tmpl[ref].add(artigo["id"])

        indice_variante = defaultdict(set)
        for variante in Prod.search_read([("default_code", "!=", False)], ["default_code", "product_tmpl_id"]):
            ref = normalizar(variante["default_code"])
            if len(ref) >= MIN_REF:
                indice_tmpl[ref].add(variante["product_tmpl_id"][0])
                indice_variante[ref].add(variante["id"])
        return indice_tmpl, indice_variante

    def _mapa_documentos_vivos(self, orfaos):
        """O que já está no sítio: os conteúdos e os nomes, por artigo.

        É contra isto que se decide se um órfão é uma recuperação ou entulho. O
        conjunto dos `checksum` é o que decide de facto — ver a nota no topo.
        """
        Doc = self.env["product.document"].sudo().with_context(active_test=False)
        vivos = Doc.search([("id", "not in", orfaos.ids)]) if orfaos else Doc.browse()
        checksums_vivos = {d.checksum for d in vivos if d.checksum}

        artigo_por_variante = self._artigo_por_variante(
            [d.res_id for d in vivos if d.res_model == "product.product" and d.res_id]
        )

        por_drive = defaultdict(list)
        por_artigo = defaultdict(list)
        for doc in vivos:
            if doc.gdrive_file_id:
                por_drive[doc.gdrive_file_id].append(doc.id)
            if doc.res_model == "product.template":
                artigo = doc.res_id
            else:
                artigo = artigo_por_variante.get(doc.res_id)
            if artigo:
                nome, tipo = sem_prefixo_tipo(doc.name)
                por_artigo[artigo].append((normalizar(nome), tipo, doc.name, doc.write_date))
        return checksums_vivos, por_artigo

    @api.model
    def _artigo_por_variante(self, ids_variante):
        """variante -> artigo, de uma só vez.

        Resolver isto documento a documento seria uma consulta por registo sobre os
        milhares de documentos vivos da base; o censo passaria a demorar minutos.
        """
        if not ids_variante:
            return {}
        variantes = self.env["product.product"].sudo().with_context(active_test=False).search_read(
            [("id", "in", list(set(ids_variante)))], ["product_tmpl_id"],
        )
        return {v["id"]: v["product_tmpl_id"][0] for v in variantes if v["product_tmpl_id"]}

    def _classificar(self, doc, indice_tmpl, indice_variante, refs_ordenadas, checksums_vivos, docs_por_artigo):
        nome_limpo, tipo = sem_prefixo_tipo(doc.name)
        redundante = bool(doc.checksum and doc.checksum in checksums_vivos)
        linha = {
            "doc_id": doc.id,
            "nome_ficheiro": doc.name or "",
            "tipo_documento": tipo,
            "res_model_origem": doc.res_model,
            "res_id_morto": doc.res_id,
            "gdrive_file_id": doc.gdrive_file_id or "",
            "checksum": doc.checksum or "",
            "unico": not redundante,
        }

        # O conteúdo decide antes de tudo o resto. Se o mesmo ficheiro já está
        # colocado e acessível, este órfão não é nada para recuperar: é entulho das
        # importações repetidas, e sai de circulação sem se perder nada.
        if redundante:
            linha["estado"] = "duplicado_conteudo"
            return linha

        ref, artigos = self._procurar_referencia(nome_limpo, indice_tmpl, refs_ordenadas)
        linha["referencia"] = ref or ""
        if not ref:
            linha["estado"] = "sem_referencia"
            return linha
        if len(artigos) > 1:
            linha["estado"] = "ambiguo"
            linha["artigos_ambiguos"] = ", ".join(str(i) for i in sorted(artigos))
            return linha

        artigo_id = next(iter(artigos))
        linha["artigo_id"] = artigo_id
        variantes = indice_variante.get(ref, set())
        linha["variante_id"] = next(iter(variantes)) if len(variantes) == 1 else False

        alvo = normalizar(nome_limpo)
        atuais = docs_por_artigo.get(artigo_id, ())

        # O nome igual decide-se primeiro, mesmo que apareça depois na lista: é o
        # diagnóstico mais preciso dos dois e não deve ficar escondido atrás do outro.
        for nome_vivo, _tipo_vivo, nome_original, _escrito_em in atuais:
            if nome_vivo == alvo:
                linha["estado"] = "duplicado_nome"
                linha["ja_existe_como"] = nome_original
                return linha

        for _nome_vivo, tipo_vivo, nome_original, escrito_em in atuais:
            if tipo and tipo_vivo == tipo:
                # Mesmo artigo, mesmo tipo de documento, ficheiro diferente. Pode ser
                # a versão que a Ana substituiu à mão — e pode ser um documento
                # legítimo a mais. Não se decide aqui; decide-se olhando.
                linha["estado"] = "versao_antiga"
                linha["ja_existe_como"] = nome_original
                linha["alvo_escrito_em"] = escrito_em
                return linha

        linha["estado"] = "ligavel"
        return linha

    @api.model
    def _procurar_referencia(self, nome_ficheiro, indice, refs_ordenadas):
        """A referência mais longa contida no nome do ficheiro.

        A mais longa primeiro de propósito: com 'FA100' e 'FA1000' na base, o ficheiro
        'FA1000_ficha.pdf' contém as duas e a certa é a comprida.
        """
        alvo = normalizar(nome_ficheiro)
        for ref in refs_ordenadas:
            if ref in alvo:
                return ref, indice[ref]
        return None, set()

    @api.model
    def _contar_imagens_sem_produto(self):
        return self.env["product.image"].sudo().with_context(active_test=False).search_count([
            ("product_tmpl_id", "=", False), ("product_variant_id", "=", False),
        ])

    # ---------------------------------------------------------------- aplicar

    def action_aprovar_recuperaveis(self):
        """Marca as linhas recuperáveis para revisão — não escreve nos documentos."""
        for censo in self:
            censo.linha_ids.filtered(lambda l: l.estado == "ligavel").aprovado = True
        return True

    def action_aplicar(self):
        self.ensure_one()
        linhas = self.linha_ids.filtered(lambda l: l.aprovado and not l.aplicado_em)
        if not linhas:
            raise UserError(_("Não há nenhuma linha aprovada por aplicar."))
        nao_recuperaveis = linhas.filtered(lambda l: l.estado != "ligavel")
        if nao_recuperaveis:
            raise UserError(_(
                "%d linhas aprovadas não estão marcadas como recuperáveis. Só se religa "
                "o que a análise deu como seguro; o resto tem de ser resolvido à mão.",
                len(nao_recuperaveis),
            ))

        aplicados = 0
        for linha in linhas:
            if linha._religar():
                aplicados += 1
        self.n_aplicados += aplicados
        if aplicados:
            self.state = "aplicado"
        _logger.info(
            "pg_product_update: censo %s — %s documentos religados de %s aprovados.",
            self.id, aplicados, len(linhas),
        )
        return True


class PgDocumentoOrfaoLinha(models.Model):
    _name = "pg.documento.orfao.linha"
    _description = "Documento orfao analisado"
    _order = "estado, id"

    censo_id = fields.Many2one("pg.documento.orfao.censo", required=True, ondelete="cascade", index=True)

    # `doc_id` é um inteiro e não um many2one de propósito: mostrar um many2one na
    # lista obriga o Odoo a ler o documento para calcular o nome, e ler um órfão é
    # precisamente o que rebenta com AccessError. O nome fica aqui em cópia.
    doc_id = fields.Integer("Documento", required=True, readonly=True)
    nome_ficheiro = fields.Char(readonly=True)
    tipo_documento = fields.Char(readonly=True)
    gdrive_file_id = fields.Char("Ficheiro no Drive", readonly=True)
    checksum = fields.Char("Resumo do conteúdo", readonly=True, index=True)
    unico = fields.Boolean(
        "Sem gémeo vivo", readonly=True, index=True,
        help="O conteúdo deste ficheiro não existe em mais lado nenhum. São estes, e "
             "só estes, que se perdem de facto se os órfãos forem apagados.",
    )

    res_model_origem = fields.Char(readonly=True)
    res_id_morto = fields.Integer("Registo inexistente", readonly=True)

    referencia = fields.Char(readonly=True)
    artigo_id = fields.Many2one("product.template", "Artigo de destino", readonly=True, ondelete="set null")
    variante_id = fields.Many2one("product.product", "Variante de destino", readonly=True, ondelete="set null")
    artigos_ambiguos = fields.Char(readonly=True)
    ja_existe_como = fields.Char("O artigo já tem", readonly=True)
    alvo_escrito_em = fields.Datetime("Alterado em", readonly=True)

    estado = fields.Selection(ESTADOS, required=True, readonly=True, index=True)
    aprovado = fields.Boolean(
        help="Só o que estiver aprovado é religado, e mesmo assim a verificação é "
             "repetida no momento da escrita.",
    )
    aplicado_em = fields.Datetime(readonly=True)
    resultado = fields.Char(readonly=True)

    def _religar(self):
        """Liga o documento ao destino. Não apaga nem substitui nada.

        Revalida tudo agora: entre o censo e este clique podem ter passado dias, e
        alguém pode ter colocado à mão o ficheiro que aqui se ia acrescentar.
        """
        self.ensure_one()
        Doc = self.env["product.document"].sudo().with_context(active_test=False)
        doc = Doc.browse(self.doc_id)
        if not doc.exists():
            self.write({"resultado": _("documento já não existe"), "aplicado_em": fields.Datetime.now()})
            return False

        artigo = self.artigo_id
        if not artigo.exists():
            self.write({"resultado": _("artigo de destino já não existe"), "aplicado_em": fields.Datetime.now()})
            return False

        conflito = self._conflito_atual(doc, artigo)
        if conflito:
            self.write({
                "estado": "duplicado_nome", "aprovado": False, "ja_existe_como": conflito,
                "resultado": _("não aplicado: o artigo entretanto passou a ter este ficheiro"),
                "aplicado_em": fields.Datetime.now(),
            })
            return False

        variante = self.variante_id if self.variante_id.exists() else False
        vals = {
            "res_model": "product.product" if variante else "product.template",
            "res_id": variante.id if variante else artigo.id,
        }
        vals.update(self._valores_invisiveis(doc))
        doc.write(vals)
        self.write({
            "aplicado_em": fields.Datetime.now(),
            "resultado": _("ligado a %s") % (variante.display_name if variante else artigo.display_name),
        })
        return True

    def _conflito_atual(self, doc, artigo):
        """O artigo já tem este ficheiro? Devolve o nome do que lá está, ou nada."""
        Doc = self.env["product.document"].sudo().with_context(active_test=False)
        variantes = artigo.with_context(active_test=False).product_variant_ids
        atuais = Doc.search([
            "|",
            "&", ("res_model", "=", "product.template"), ("res_id", "=", artigo.id),
            "&", ("res_model", "=", "product.product"), ("res_id", "in", variantes.ids),
        ]) - doc

        nome_limpo, _tipo = sem_prefixo_tipo(doc.name)
        alvo = normalizar(nome_limpo)
        for atual in atuais:
            if doc.gdrive_file_id and atual.gdrive_file_id == doc.gdrive_file_id:
                return atual.name
            nome_atual, _t = sem_prefixo_tipo(atual.name)
            if normalizar(nome_atual) == alvo:
                return atual.name
        return None

    @api.model
    def _valores_invisiveis(self, doc):
        """Recuperar devolve o acesso pelo Odoo; não muda o que o cliente vê.

        Os campos de visibilidade são personalizações desta base e podem não existir
        noutra, daí a verificação em `_fields` em vez de os assumir.
        """
        vals = {}
        campos = doc._fields
        if "shown_on_product_page" in campos:
            vals["shown_on_product_page"] = False
        if "attached_on_sale" in campos:
            # A seleção pode ser uma lista ou um método; só se sabe o que lá está
            # perguntando ao próprio campo.
            opcoes = dict(campos["attached_on_sale"]._description_selection(self.env) or [])
            if "hidden" in opcoes:
                vals["attached_on_sale"] = "hidden"
        return vals
