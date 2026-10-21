# -*- coding: utf-8 -*-
"""Gera a tabela de preços em Excel, com a imagem de cada artigo na linha."""

import base64
import io
import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# A imagem ocupa uma célula. Estes números são o compromisso entre ler-se bem e
# o ficheiro não crescer sem controlo: 64 pontos de altura de linha dão cerca de
# 85 píxeis, e a `image_256` cabe lá dentro reduzida a metade.
ALTURA_LINHA_COM_IMAGEM = 64
LARGURA_COLUNA_IMAGEM = 14
ESCALA_IMAGEM = 0.33

# Formatos que o xlsxwriter embute sem conversão, reconhecidos pelos primeiros
# bytes. O nome do ficheiro não conta: quem decide é o conteúdo.
ASSINATURAS_DIRETAS = (b"\x89PNG", b"\xff\xd8\xff", b"GIF8", b"BM")


class PgTabelaPrecos(models.TransientModel):
    _name = "pg.tabela.precos"
    _description = "Tabela de preços em Excel"

    categoria_ids = fields.Many2many(
        "product.category", string="Categorias",
        help="Deixar vazio inclui todas as categorias.",
    )
    lista_preco_id = fields.Many2one(
        "product.pricelist", string="Lista de preços",
        help="Sem lista, usa-se o preço de venda do artigo.",
    )
    incluir_imagens = fields.Boolean(
        string="Incluir imagens", default=True,
        help="Sem imagens o ficheiro gera-se muito mais depressa.",
    )
    detalhe = fields.Selection(
        [("variante", "Por variante"), ("artigo", "Por artigo")],
        string="Detalhe", default="variante", required=True,
        help="A referência de venda vive quase sempre na variante, não no artigo. "
             "Por artigo sai uma lista mais curta, mas muitos artigos aparecem "
             "sem referência nenhuma.",
    )
    apenas_vendaveis = fields.Boolean(
        string="Apenas artigos à venda", default=True,
        help="Deixa de fora os artigos que não estão marcados para venda.",
    )
    ficheiro = fields.Binary(string="Ficheiro", readonly=True, attachment=False)
    nome_ficheiro = fields.Char(string="Nome do ficheiro", readonly=True)
    diagnostico = fields.Text(
        string="Imagens ignoradas", readonly=True,
        help="Que artigos ficaram sem foto na tabela, e porquê.",
    )

    def _modelo(self):
        """`product.product` sao as variantes; `product.template` sao os artigos."""
        return "product.product" if self.detalhe == "variante" else "product.template"

    def _dominio_artigos(self):
        """O conjunto de artigos ou variantes que entra na tabela.

        O dominio e o mesmo nos dois modelos: `categ_id` e `sale_ok` existem em
        ambos, e na variante apontam para os do artigo de que ela descende.
        """
        dominio = []
        if self.categoria_ids:
            # `child_of` para que escolher uma família traga as subfamílias com ela:
            # quem escolhe "Perfis LED" quer os acessórios dos perfis também.
            dominio.append(("categ_id", "child_of", self.categoria_ids.ids))
        if self.apenas_vendaveis:
            dominio.append(("sale_ok", "=", True))
        return dominio

    def _imagem_para_xlsx(self, dados_base64, motivos):
        """Bytes que o xlsxwriter aceita, ou None se a imagem não servir.

        Duas razões para isto existir, ambas descobertas a gerar uma tabela real:

        O Odoo guarda muitas imagens em **WEBP** -- nos Transformadores eram 4 em
        13 -- e o xlsxwriter não conhece esse formato. Convertem-se para PNG.

        E a validação tem de acontecer **aqui**, antes de entregar seja o que for
        ao xlsxwriter. O `insert_image` não lê a imagem: só a regista, e o erro só
        rebenta no `close()`, quando já não há linha a que o atribuir. Um try/except
        à volta do `insert_image` não apanha nada, e uma única imagem má derrubava
        o ficheiro inteiro.
        """
        if not dados_base64:
            return None
        try:
            bruto = base64.b64decode(dados_base64)
        except Exception:
            motivos.append("base64 ilegivel")
            return None
        if bruto.startswith(ASSINATURAS_DIRETAS):
            return bruto
        try:
            from PIL import Image
            origem = Image.open(io.BytesIO(bruto))
            if origem.mode not in ("RGB", "RGBA"):
                origem = origem.convert("RGBA" if "A" in origem.mode else "RGB")
            destino = io.BytesIO()
            origem.save(destino, format="PNG")
            return destino.getvalue()
        except Exception as erro:
            # A razao interessa, e tem de ser legivel por quem gera a tabela. O erro
            # cru do Pillow -- "cannot identify image file <BytesIO object at 0x...>"
            # -- nao diz nada a ninguem. Medido na base de testes a 03/10: as quatro
            # imagens que faltavam eram todas WEBP, e o Pillow do servidor nao traz
            # descodificador para esse formato. Nao ha alternativa dentro do Odoo:
            # a image_1920, a 512, a 256 e a 128 sao todas WEBP para esses artigos.
            if bruto[:4] == b"RIFF" and bruto[8:12] == b"WEBP":
                motivos.append(_(
                    "imagens WEBP: o servidor não traz leitor para este formato"))
            else:
                motivos.append("%s: %s" % (type(erro).__name__, str(erro)[:100]))
            return None

    def _imagem_do_artigo(self, artigo, motivos):
        """A imagem a usar na linha, com recurso a do artigo-pai quando precisa.

        Uma variante pode ter fotografia propria. Quando essa nao se consegue ler
        -- hoje, porque esta em WEBP e o servidor nao traz leitor -- a linha ficava
        vazia, mesmo havendo a do artigo-pai perfeitamente legivel ao lado.

        Medido em producao a 07/10: das 359 variantes com imagem propria ilegivel,
        **350 tem o artigo-pai com imagem que se le**. Recorrer a ela recupera 97%
        das fotografias sem tocar numa unica linha do catalogo.

        Nao se perde nada: a imagem propria da variante fica onde esta, e volta a
        ser usada sozinha no dia em que o servidor a souber ler. O recurso so entra
        quando a primeira falha.

        Devolve (bytes, usou_recurso).
        """
        imagem = self._imagem_para_xlsx(artigo.image_256, motivos)
        if imagem or artigo._name != "product.product":
            return imagem, False
        # A `image_256` da variante ja e a do artigo quando a variante nao tem
        # imagem propria -- se falhou, e porque tem uma, e e essa que nao se le.
        pai = artigo.product_tmpl_id
        if not pai.image_256:
            return None, False
        # Motivos a parte: o do artigo-pai nao interessa a quem le o aviso.
        imagem = self._imagem_para_xlsx(pai.image_256, [])
        return imagem, bool(imagem)

    def _preco(self, artigo):
        """O preço, pela lista escolhida ou pelo preço de venda.

        Na variante usa-se o `lst_price`, que e o preco do artigo mais o que os
        valores de atributo lhe acrescentam. O `list_price` da variante devolveria
        o do artigo e ignorava esses extras.
        """
        if not self.lista_preco_id:
            return artigo.lst_price if artigo._name == "product.product" else artigo.list_price
        return self.lista_preco_id._get_product_price(artigo, 1.0)

    def _descricao(self, artigo):
        """O nome, com os valores de atributo quando se trata de uma variante.

        Sem isto, as variantes do mesmo artigo saem todas com a mesma descricao e
        so se distinguem pela referencia -- que e precisamente o que a cliente
        queria ver, mas nao chega para quem le a tabela.
        """
        nome = artigo.name or ""
        if artigo._name != "product.product":
            return nome
        valores = artigo.product_template_attribute_value_ids.mapped("name")
        return "%s (%s)" % (nome, ", ".join(valores)) if valores else nome

    def action_gerar(self):
        self.ensure_one()
        try:
            import xlsxwriter
        except ImportError:  # pragma: no cover - dependência do próprio Odoo
            raise UserError(_(
                "Falta a biblioteca xlsxwriter no servidor. É dependência do "
                "Odoo, por isso isto não devia acontecer — avisar quem gere o "
                "alojamento."))

        # Lista local, passada a quem precisa: um recordset do Odoo nao aceita
        # atributos avulsos, e guardar estado nele nao sobrevive a um `browse`.
        motivos = []
        artigos = self.env[self._modelo()].search(
            self._dominio_artigos(), order="categ_id, default_code, name")
        if not artigos:
            raise UserError(_("Não há artigos para os critérios escolhidos."))

        memoria = io.BytesIO()
        livro = xlsxwriter.Workbook(memoria, {"in_memory": True})
        folha = livro.add_worksheet(_("Tabela de preços"))

        titulo = livro.add_format({
            "bold": True, "font_size": 16, "valign": "vcenter"})
        subtitulo = livro.add_format({"font_size": 9, "font_color": "#666666"})
        cabecalho = livro.add_format({
            "bold": True, "font_color": "#FFFFFF", "bg_color": "#2F5597",
            "align": "center", "valign": "vcenter", "border": 1})
        familia = livro.add_format({
            "bold": True, "bg_color": "#E8EDF5", "border": 1, "valign": "vcenter"})
        celula = livro.add_format({"valign": "vcenter", "border": 1})
        celula_quebra = livro.add_format({
            "valign": "vcenter", "border": 1, "text_wrap": True})
        moeda = livro.add_format({
            "valign": "vcenter", "border": 1, "num_format": "#,##0.00 €",
            "align": "right"})

        empresa = self.env.company
        folha.merge_range(0, 0, 0, 5, empresa.name, titulo)
        contexto = [fields.Date.context_today(self).strftime("%d/%m/%Y")]
        if self.lista_preco_id:
            contexto.append(self.lista_preco_id.name)
        if self.categoria_ids:
            contexto.append(", ".join(self.categoria_ids.mapped("name")))
        contexto.append(
            _("por variante") if self.detalhe == "variante" else _("por artigo"))
        folha.merge_range(1, 0, 1, 5, " · ".join(contexto), subtitulo)

        colunas = [
            (_("Nº"), 5), (_("Referência"), 22),
            (_("Imagem"), LARGURA_COLUNA_IMAGEM), (_("Descrição"), 60),
            (_("Un."), 8), (_("Preço"), 14),
        ]
        linha_cabecalho = 3
        for indice, (nome, largura) in enumerate(colunas):
            folha.set_column(indice, indice, largura)
            folha.write(linha_cabecalho, indice, nome, cabecalho)
        folha.freeze_panes(linha_cabecalho + 1, 0)

        linha = linha_cabecalho + 1
        numero = 0
        imagens = ignoradas = recorridas = 0
        categoria_atual = None
        for artigo in artigos:
            if artigo.categ_id != categoria_atual:
                categoria_atual = artigo.categ_id
                folha.merge_range(
                    linha, 0, linha, len(colunas) - 1,
                    categoria_atual.complete_name or categoria_atual.name, familia)
                linha += 1
            numero += 1
            if self.incluir_imagens:
                folha.set_row(linha, ALTURA_LINHA_COM_IMAGEM)
            folha.write(linha, 0, numero, celula)
            folha.write(linha, 1, artigo.default_code or "", celula)
            folha.write(linha, 2, "", celula)
            folha.write(linha, 3, self._descricao(artigo), celula_quebra)
            folha.write(linha, 4, artigo.uom_id.name or "", celula)
            folha.write(linha, 5, self._preco(artigo), moeda)
            if self.incluir_imagens:
                # Um artigo com imagem ilegível não pode fazer cair a tabela toda:
                # a linha fica sem imagem e o resto do ficheiro sai à mesma.
                imagem, por_recurso = self._imagem_do_artigo(artigo, motivos)
                if por_recurso:
                    recorridas += 1
                if imagem:
                    folha.insert_image(
                        linha, 2, "%s.png" % (artigo.default_code or artigo.id),
                        {
                            "image_data": io.BytesIO(imagem),
                            "x_scale": ESCALA_IMAGEM, "y_scale": ESCALA_IMAGEM,
                            "x_offset": 6, "y_offset": 4, "object_position": 1,
                        })
                    imagens += 1
                elif artigo.image_256:
                    ignoradas += 1
            linha += 1

        folha.autofilter(linha_cabecalho, 0, linha - 1, len(colunas) - 1)
        livro.close()
        if ignoradas or recorridas:
            # Fica no log, não em exceção: a tabela saiu, e saber que três artigos
            # ficaram sem foto é informação, não motivo para não entregar nada.
            _logger.info(
                "pg_tabela_precos: %d imagens embutidas (%d por recurso ao artigo), "
                "%d ignoradas por não serem legíveis.", imagens, recorridas, ignoradas)

        nome = "Tabela_de_precos_%s.xlsx" % fields.Date.context_today(self)
        avisos = []
        if recorridas:
            avisos.append(_(
                "%s variantes aparecem com a fotografia do artigo, por a sua "
                "própria não se conseguir ler.") % recorridas)
        if ignoradas:
            vistos = list(dict.fromkeys(motivos))[:5]
            avisos.append(_(
                "%(n)s de %(t)s artigos ficaram sem foto nenhuma.\n%(m)s\n"
                "As linhas desses artigos saem na mesma, só sem imagem."
            ) % {"n": ignoradas, "t": imagens + ignoradas, "m": "\n".join(vistos)})
        resumo = "\n\n".join(avisos) if avisos else False
        self.write({
            "ficheiro": base64.b64encode(memoria.getvalue()),
            "nome_ficheiro": nome,
            "diagnostico": resumo,
        })
        memoria.close()
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/?model=%s&id=%s&field=ficheiro"
                   "&filename_field=nome_ficheiro&download=true" % (self._name, self.id),
            "target": "self",
        }
