# -*- coding: utf-8 -*-
"""O que estes testes guardam.

A tabela é um ficheiro binário: ninguém a revê em diff e ninguém dá pela diferença
entre um .xlsx certo e um .xlsx com uma coluna trocada. Por isso os testes abrem o
ficheiro gerado e verificam o que lá está dentro, em vez de se contentarem com o
facto de a geração não ter rebentado.
"""

import base64
import io
import zipfile

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTabelaPrecos(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.familia = cls.env["product.category"].create({"name": "Família de teste"})
        cls.subfamilia = cls.env["product.category"].create(
            {"name": "Subfamília de teste", "parent_id": cls.familia.id})
        # 1x1 píxel PNG: chega para provar que a imagem entra no ficheiro.
        cls.png = base64.b64encode(base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8"
            "z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="))
        cls.artigo = cls.env["product.template"].create({
            "name": "Artigo com imagem", "default_code": "TST-001",
            "categ_id": cls.familia.id, "list_price": 12.34,
            "image_1920": cls.png, "sale_ok": True,
        })
        cls.artigo_subfamilia = cls.env["product.template"].create({
            "name": "Artigo da subfamília", "default_code": "TST-002",
            "categ_id": cls.subfamilia.id, "list_price": 56.78, "sale_ok": True,
        })
        cls.artigo_nao_vendavel = cls.env["product.template"].create({
            "name": "Artigo fora de venda", "default_code": "TST-003",
            "categ_id": cls.familia.id, "list_price": 99.0, "sale_ok": False,
        })

    def _gerar(self, **valores):
        assistente = self.env["pg.tabela.precos"].create(valores)
        assistente.action_gerar()
        self.assertTrue(assistente.ficheiro, "O assistente não produziu ficheiro.")
        return assistente, base64.b64decode(assistente.ficheiro)

    def test_ficheiro_e_um_xlsx_valido(self):
        assistente, conteudo = self._gerar(categoria_ids=[(6, 0, self.familia.ids)])
        with zipfile.ZipFile(io.BytesIO(conteudo)) as z:
            nomes = z.namelist()
        self.assertIn("xl/workbook.xml", nomes)
        self.assertTrue(assistente.nome_ficheiro.endswith(".xlsx"))

    def test_imagem_entra_no_ficheiro(self):
        """Era isto que a exportação normal do Odoo não fazia, e é o pedido todo."""
        _, conteudo = self._gerar(
            categoria_ids=[(6, 0, self.familia.ids)], incluir_imagens=True)
        with zipfile.ZipFile(io.BytesIO(conteudo)) as z:
            media = [n for n in z.namelist() if n.startswith("xl/media/")]
        self.assertTrue(media, "Nenhuma imagem foi embutida no ficheiro.")

    def test_sem_imagens_nao_embute_nada(self):
        _, conteudo = self._gerar(
            categoria_ids=[(6, 0, self.familia.ids)], incluir_imagens=False)
        with zipfile.ZipFile(io.BytesIO(conteudo)) as z:
            media = [n for n in z.namelist() if n.startswith("xl/media/")]
        self.assertFalse(media)

    def test_escolher_uma_familia_traz_as_subfamilias(self):
        """Quem escolhe 'Perfis LED' quer os acessórios dos perfis também."""
        assistente = self.env["pg.tabela.precos"].create(
            {"categoria_ids": [(6, 0, self.familia.ids)]})
        artigos = self.env["product.template"].search(assistente._dominio_artigos())
        self.assertIn(self.artigo_subfamilia, artigos)

    def test_apenas_vendaveis_deixa_de_fora_os_outros(self):
        assistente = self.env["pg.tabela.precos"].create(
            {"categoria_ids": [(6, 0, self.familia.ids)], "apenas_vendaveis": True})
        artigos = self.env["product.template"].search(assistente._dominio_artigos())
        self.assertNotIn(self.artigo_nao_vendavel, artigos)

        assistente.apenas_vendaveis = False
        artigos = self.env["product.template"].search(assistente._dominio_artigos())
        self.assertIn(self.artigo_nao_vendavel, artigos)

    def test_sem_artigos_avisa_em_vez_de_entregar_folha_vazia(self):
        vazia = self.env["product.category"].create({"name": "Família sem artigos"})
        assistente = self.env["pg.tabela.precos"].create(
            {"categoria_ids": [(6, 0, vazia.ids)]})
        with self.assertRaises(UserError):
            assistente.action_gerar()

    def test_preco_segue_a_lista_escolhida(self):
        lista = self.env["product.pricelist"].create({
            "name": "Lista de teste",
            "item_ids": [(0, 0, {
                "applied_on": "3_global", "compute_price": "percentage",
                "percent_price": 50,
            })],
        })
        assistente = self.env["pg.tabela.precos"].create({
            "categoria_ids": [(6, 0, self.familia.ids)],
            "lista_preco_id": lista.id,
        })
        self.assertAlmostEqual(assistente._preco(self.artigo), 6.17, places=2)

    def test_imagem_webp_e_convertida_e_nao_derruba_o_ficheiro(self):
        """O defeito que uma tabela real destapou, e que os testes não apanhavam.

        O Odoo guarda muitas imagens em WEBP — nos Transformadores da Essani eram
        4 em 13 — e o xlsxwriter não conhece esse formato. Pior: o `insert_image`
        não lê a imagem, só a regista, e o erro só rebenta no `close()`. Uma única
        imagem WEBP fazia cair a tabela inteira com "Unknown or unsupported image
        file format", sem indicação de qual era o artigo.
        """
        from PIL import Image
        memoria = io.BytesIO()
        try:
            Image.new("RGB", (4, 4), (200, 30, 30)).save(memoria, format="WEBP")
        except Exception:
            self.skipTest("Esta instalação do Pillow não grava WEBP.")
        webp = base64.b64encode(memoria.getvalue())

        artigo = self.env["product.template"].create({
            "name": "Artigo com imagem WEBP", "default_code": "TST-WEBP",
            "categ_id": self.familia.id, "list_price": 10.0,
            "image_1920": webp, "sale_ok": True,
        })
        self.assertTrue(artigo.image_256)

        _, conteudo = self._gerar(categoria_ids=[(6, 0, self.familia.ids)])
        with zipfile.ZipFile(io.BytesIO(conteudo)) as z:
            media = [n for n in z.namelist() if n.startswith("xl/media/")]
        self.assertTrue(media, "A tabela com WEBP não embutiu imagem nenhuma.")

    def test_imagem_ilegivel_nao_impede_a_tabela(self):
        """Uma imagem corrompida tira a foto àquela linha, não a tabela a ninguém."""
        assistente = self.env["pg.tabela.precos"].create({})
        motivos = []
        self.assertIsNone(
            assistente._imagem_para_xlsx(base64.b64encode(b"nao sou imagem"), motivos))
        self.assertIsNone(assistente._imagem_para_xlsx(False, motivos))
        self.assertTrue(motivos, "A razão da imagem rejeitada não foi registada.")

        self.env["product.template"].create({
            "name": "Artigo com imagem partida", "default_code": "TST-MAU",
            "categ_id": self.familia.id, "list_price": 1.0, "sale_ok": True,
        })
        _, conteudo = self._gerar(categoria_ids=[(6, 0, self.familia.ids)])
        with zipfile.ZipFile(io.BytesIO(conteudo)) as z:
            self.assertIn("xl/workbook.xml", z.namelist())

    def _com_variantes(self):
        """Um artigo com duas variantes, cada uma com a sua referência.

        É o caso que a Ana Valente apontou: a referência de venda vive na variante
        e o artigo-pai nem sempre tem uma.
        """
        atributo = self.env["product.attribute"].create({
            "name": "Comprimento de teste",
            "value_ids": [(0, 0, {"name": "1m"}), (0, 0, {"name": "2m"})],
        })
        modelo = self.env["product.template"].create({
            "name": "Perfil com variantes", "categ_id": self.familia.id,
            "list_price": 20.0, "sale_ok": True,
            "attribute_line_ids": [(0, 0, {
                "attribute_id": atributo.id,
                "value_ids": [(6, 0, atributo.value_ids.ids)],
            })],
        })
        for indice, variante in enumerate(modelo.product_variant_ids, start=1):
            variante.default_code = "VAR-%s" % indice
        return modelo

    def test_por_variante_traz_as_referencias_das_variantes(self):
        """O pedido da cliente a 06/10, nove minutos depois de ver a primeira tabela."""
        modelo = self._com_variantes()
        self.assertEqual(len(modelo.product_variant_ids), 2)

        assistente = self.env["pg.tabela.precos"].create({
            "categoria_ids": [(6, 0, self.familia.ids)], "detalhe": "variante"})
        variantes = self.env[assistente._modelo()].search(assistente._dominio_artigos())

        self.assertEqual(assistente._modelo(), "product.product")
        self.assertTrue(modelo.product_variant_ids <= variantes)
        self.assertEqual(
            set(modelo.product_variant_ids.mapped("default_code")), {"VAR-1", "VAR-2"})

    def test_por_artigo_traz_uma_linha_so(self):
        """A opção antiga continua a existir, para quem quer a lista curta."""
        modelo = self._com_variantes()
        assistente = self.env["pg.tabela.precos"].create({
            "categoria_ids": [(6, 0, self.familia.ids)], "detalhe": "artigo"})
        artigos = self.env[assistente._modelo()].search(assistente._dominio_artigos())

        self.assertEqual(assistente._modelo(), "product.template")
        self.assertIn(modelo, artigos)

    def test_descricao_da_variante_distingue_as_variantes(self):
        """Sem os valores de atributo, as variantes saem todas com o mesmo nome."""
        modelo = self._com_variantes()
        assistente = self.env["pg.tabela.precos"].create({"detalhe": "variante"})
        descricoes = {assistente._descricao(v) for v in modelo.product_variant_ids}

        self.assertEqual(len(descricoes), 2, "As duas variantes saíram com o mesmo nome.")
        self.assertTrue(all("Perfil com variantes" in d for d in descricoes))

    def test_ficheiro_por_variante_gera(self):
        self._com_variantes()
        _, conteudo = self._gerar(
            categoria_ids=[(6, 0, self.familia.ids)], detalhe="variante")
        with zipfile.ZipFile(io.BytesIO(conteudo)) as z:
            self.assertIn("xl/workbook.xml", z.namelist())

    def test_variante_com_imagem_ilegivel_recorre_a_do_artigo(self):
        """Medido em produção a 07/10: das 359 variantes com imagem própria que o
        servidor não lê, 350 têm o artigo-pai com imagem legível. Recorrer a ela
        recupera 97% das fotografias sem tocar numa linha do catálogo.
        """
        from PIL import Image
        memoria = io.BytesIO()
        try:
            Image.new("RGB", (4, 4), (10, 90, 10)).save(memoria, format="WEBP")
        except Exception:
            self.skipTest("Esta instalação do Pillow não grava WEBP.")

        atributo = self.env["product.attribute"].create({
            "name": "Acabamento de teste",
            "value_ids": [(0, 0, {"name": "Mate"}), (0, 0, {"name": "Brilho"})],
        })
        modelo = self.env["product.template"].create({
            "name": "Artigo com variantes e fotos", "categ_id": self.familia.id,
            "list_price": 30.0, "sale_ok": True, "image_1920": self.png,
            "attribute_line_ids": [(0, 0, {
                "attribute_id": atributo.id,
                "value_ids": [(6, 0, atributo.value_ids.ids)],
            })],
        })
        variante = modelo.product_variant_ids[0]
        # A variante fica com fotografia propria que o xlsxwriter nao aceita.
        variante.image_variant_1920 = base64.b64encode(memoria.getvalue())

        assistente = self.env["pg.tabela.precos"].create({"detalhe": "variante"})
        motivos = []
        imagem, por_recurso = assistente._imagem_do_artigo(variante, motivos)

        self.assertTrue(imagem, "A variante ficou sem imagem havendo a do artigo.")
        self.assertTrue(por_recurso, "Não assinalou que recorreu à imagem do artigo.")

    def test_recurso_nao_se_aplica_a_artigos(self):
        """Um artigo não tem a quem recorrer: ou a sua imagem se lê, ou não há foto."""
        artigo = self.env["product.template"].create({
            "name": "Artigo sem variantes", "categ_id": self.familia.id,
            "list_price": 5.0, "sale_ok": True, "image_1920": self.png,
        })
        assistente = self.env["pg.tabela.precos"].create({"detalhe": "artigo"})
        imagem, por_recurso = assistente._imagem_do_artigo(artigo, [])

        self.assertTrue(imagem)
        self.assertFalse(por_recurso)
