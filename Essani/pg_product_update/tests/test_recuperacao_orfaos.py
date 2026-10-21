# -*- coding: utf-8 -*-
"""A recuperação dos órfãos tem de ser prudente, não eficaz.

A Ana Valente pediu isto por escrito a 18/09: os ficheiros vieram de importações que
correram mal, ela substituiu vários à mão desde então, e repor às cegas faria a versão
velha reaparecer ao lado da nova. O perigo não é deixar documentos por recuperar — é
recuperar um a mais e alguém enviar ao cliente o ficheiro errado.

Cada teste aqui fixa uma das condições que ela pôs. Os que interessam mais não são os
que provam que o religar funciona, são os que provam que **não** acontece.

Nota sobre o alcance: os testes chamam `_analisar` com os documentos que criaram, em
vez de `action_analisar`. As bases de teste do Odoo.sh são restauradas da produção e
arrastam os 5697 órfãos reais; um teste que olhasse para toda a base falharia sempre,
como já aconteceu uma vez (commit 315d0c5).
"""

import base64

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestRecuperacaoOrfaos(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Doc = cls.env["product.document"]
        cls.censo = cls.env["pg.documento.orfao.censo"].create({"name": "Censo de teste"})
        # Referências propositadamente improváveis: o índice é construído sobre toda a
        # base, e numa base restaurada da produção uma referência banal colidiria com
        # artigos reais e daria ambiguidade onde o teste não a quer.
        cls.artigo = cls.env["product.template"].create({
            "name": "Fonte de ensaio", "default_code": "ZZORF-1000",
        })
        cls.outro = cls.env["product.template"].create({
            "name": "Fonte de ensaio curta", "default_code": "ZZORF-100",
        })

    def _conteudo(self, nome):
        """Conteúdo distinto por ficheiro.

        Desde que a classificação passou a decidir pelo conteúdo, dois documentos de
        ensaio com os mesmos bytes ficariam marcados como cópias um do outro e os
        testes da correspondência por referência nunca chegariam a correr.
        """
        return base64.b64encode(("ensaio:" + nome).encode())

    def _orfao(self, nome, **extra):
        """Um documento preso a uma variante que não existe.

        É este o estado real em produção: não `res_id = 0`, mas um id concreto cujo
        registo foi destruído quando as variantes foram recriadas.
        """
        vals = {
            "name": nome,
            "res_model": "product.product",
            "res_id": 2 ** 31 - 1,
            "datas": self._conteudo(nome),
        }
        vals.update(extra)
        return self.Doc.create(vals)

    def _vivo(self, nome, artigo=None, **extra):
        vals = {
            "name": nome,
            "res_model": "product.template",
            "res_id": (artigo or self.artigo).id,
            "datas": self._conteudo(nome),
        }
        vals.update(extra)
        return self.Doc.create(vals)

    def _analisar(self, docs):
        self.censo._analisar(docs)
        return self.censo.linha_ids

    def _linha(self, doc):
        return self.censo.linha_ids.filtered(lambda l: l.doc_id == doc.id)

    # ------------------------------------------------------------ recuperação

    def test_orfao_com_referencia_unica_e_recuperavel(self):
        doc = self._orfao("FICHA TECNICA - ZZORF-1000 manual.pdf")
        self._analisar(doc)

        linha = self._linha(doc)
        self.assertEqual(linha.estado, "ligavel")
        self.assertEqual(linha.artigo_id, self.artigo)

        self.censo.action_aprovar_recuperaveis()
        self.censo.action_aplicar()

        self.assertEqual(doc.res_model, "product.template")
        self.assertEqual(doc.res_id, self.artigo.id)
        self.assertTrue(linha.aplicado_em)

    def test_separadores_nao_impedem_o_encontro(self):
        """'zzorf 1000' e 'ZZORF-1000' são a mesma referência."""
        doc = self._orfao("zzorf 1000 esquema.dxf")
        self._analisar(doc)
        self.assertEqual(self._linha(doc).artigo_id, self.artigo)

    def test_referencia_curta_nao_rouba_o_ficheiro_da_longa(self):
        """'ZZORF-1000...' contém 'ZZORF-100'. A certa é a comprida."""
        doc = self._orfao("ZZORF-1000_ficha.pdf")
        self._analisar(doc)

        linha = self._linha(doc)
        self.assertEqual(linha.referencia, "ZZORF1000")
        self.assertEqual(linha.artigo_id, self.artigo,
                         "O ficheiro foi parar ao artigo de referência mais curta.")

    # -------------------------------------------- o que tem de ficar de fora

    def test_ficheiro_que_ja_esta_colocado_e_redundante(self):
        """O caso que domina os dados reais: 5388 dos 5904.

        O mesmo conteúdo já está colocado e acessível noutro sítio. O órfão não é
        nada para recuperar — é entulho das importações repetidas. Religá-lo poria
        duas cópias do mesmo ficheiro no artigo.

        A primeira versão comparava o `gdrive_file_id` e apanhava zero: o mesmo
        ficheiro foi carregado para o Drive várias vezes e recebeu identificador novo
        de cada vez. O que não muda é o conteúdo.
        """
        self._vivo("FICHA TECNICA - ZZORF-1000 v2.pdf", gdrive_file_id="drive-1")
        doc = self._orfao("FICHA TECNICA - ZZORF-1000.pdf", gdrive_file_id="drive-2")
        self._analisar(doc)

        linha = self._linha(doc)
        self.assertEqual(linha.estado, "duplicado_conteudo",
                         "Conteúdo igual a um vivo tem de contar como redundante.")
        self.assertFalse(linha.unico)
        with self.assertRaises(UserError):
            linha.aprovado = True
            self.censo.action_aplicar()

    def test_ficheiro_sem_gemeo_e_marcado_como_unico(self):
        """Os que se perdem de facto. São 127 ficheiros distintos em produção."""
        doc = self._orfao("qualquer coisa sem par.pdf", datas=base64.b64encode(b"so-existe-aqui"))
        self._analisar(doc)

        linha = self._linha(doc)
        self.assertTrue(linha.unico)
        self.assertTrue(linha.checksum)
        self.assertEqual(self.censo.n_unicos_registos, 1)
        self.assertEqual(self.censo.n_unicos_ficheiros, 1)

    def test_copias_do_mesmo_ficheiro_contam_como_um_so(self):
        """516 registos únicos eram 127 ficheiros: as importações repetiram-se.

        Contar registos em vez de ficheiros multiplicava por quatro o tamanho
        aparente do problema.
        """
        conteudo = base64.b64encode(b"o-mesmo-desenho")
        docs = self._orfao("desenho.dxf", datas=conteudo) | self._orfao("desenho (1).dxf", datas=conteudo)
        self._analisar(docs)

        self.assertEqual(self.censo.n_unicos_registos, 2)
        self.assertEqual(self.censo.n_unicos_ficheiros, 1)

    def test_mesmo_nome_no_artigo_fica_de_fora(self):
        """Nome igual, conteúdo diferente — o artigo já tem um ficheiro assim.

        O conteúdo tem de ser diferente, senão quem decide é a comparação de bytes e
        esta verificação nunca chegaria a correr.
        """
        self._vivo("FICHA TECNICA - ZZORF-1000 manual.pdf",
                   datas=base64.b64encode(b"a versao que o cliente colocou"))
        doc = self._orfao("FICHA TECNICA - ZZORF-1000 manual.pdf")
        self._analisar(doc)
        self.assertEqual(self._linha(doc).estado, "duplicado_nome")

    def test_mesmo_tipo_de_documento_pede_revisao(self):
        """Ficheiro diferente, mesmo tipo, mesmo artigo: pode ser a versão antiga.

        Não se decide por código — marca-se para alguém olhar. É a diferença entre
        ser prudente e ser adivinho.
        """
        self._vivo("FICHA TECNICA - ZZORF-1000 revisto.pdf")
        doc = self._orfao("FICHA TECNICA - ZZORF-1000 antigo.pdf")
        self._analisar(doc)

        linha = self._linha(doc)
        self.assertEqual(linha.estado, "versao_antiga")
        self.assertTrue(linha.ja_existe_como)

    def test_referencia_em_dois_artigos_fica_ambigua(self):
        self.env["product.template"].create({"name": "Clone", "default_code": "ZZORF-1000"})
        doc = self._orfao("ZZORF-1000 ficha.pdf")
        self._analisar(doc)
        self.assertEqual(self._linha(doc).estado, "ambiguo")

    def test_sem_referencia_no_nome_nao_se_adivinha(self):
        doc = self._orfao("documento sem nada que identifique.pdf")
        self._analisar(doc)
        self.assertEqual(self._linha(doc).estado, "sem_referencia")

    # ------------------------------------------------------------- garantias

    def test_aplicar_recusa_o_que_a_analise_nao_deu_como_seguro(self):
        self._vivo("FICHA TECNICA - ZZORF-1000 manual.pdf",
                   datas=base64.b64encode(b"a versao que o cliente colocou"))
        doc = self._orfao("FICHA TECNICA - ZZORF-1000 manual.pdf")
        self._analisar(doc)

        self._linha(doc).aprovado = True
        with self.assertRaises(UserError):
            self.censo.action_aplicar()
        self.assertEqual(doc.res_id, 2 ** 31 - 1, "O documento foi religado à mesma.")

    def test_verificacao_repete_se_no_momento_da_escrita(self):
        """Entre o censo e o clique podem passar dias.

        Se entretanto alguém colocou o ficheiro à mão no artigo, a linha deixa de ser
        aplicável — mesmo tendo sido aprovada quando ainda era.
        """
        doc = self._orfao("FICHA TECNICA - ZZORF-1000 manual.pdf")
        self._analisar(doc)
        linha = self._linha(doc)
        self.assertEqual(linha.estado, "ligavel")
        linha.aprovado = True

        self._vivo("FICHA TECNICA - ZZORF-1000 manual.pdf")
        self.censo.action_aplicar()

        self.assertEqual(doc.res_id, 2 ** 31 - 1, "Escreveu por cima de trabalho novo.")
        self.assertEqual(linha.estado, "duplicado_nome")
        self.assertFalse(linha.aprovado)

    def test_nada_e_apagado(self):
        docs = self.Doc.search([])
        antes = len(docs)
        orfao = self._orfao("FICHA TECNICA - ZZORF-1000 manual.pdf")
        self._analisar(orfao)
        self.censo.action_aprovar_recuperaveis()
        self.censo.action_aplicar()

        self.assertEqual(len(self.Doc.search([])), antes + 1)
        self.assertTrue(orfao.exists())

    def test_recuperado_nao_muda_o_que_o_cliente_ve(self):
        """Devolver o acesso pelo Odoo não é publicar no site nem juntar a orçamentos.

        Os campos de visibilidade são personalizações desta base; onde não existirem,
        não há nada a verificar.
        """
        doc = self._orfao("FICHA TECNICA - ZZORF-1000 manual.pdf")
        if "shown_on_product_page" in doc._fields:
            doc.shown_on_product_page = True
        self._analisar(doc)
        self.censo.action_aprovar_recuperaveis()
        self.censo.action_aplicar()

        if "shown_on_product_page" in doc._fields:
            self.assertFalse(doc.shown_on_product_page)
        if "attached_on_sale" in doc._fields:
            self.assertEqual(doc.attached_on_sale, "hidden")
