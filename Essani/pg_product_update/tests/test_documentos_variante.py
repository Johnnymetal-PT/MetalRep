# -*- coding: utf-8 -*-
"""Os documentos têm de sobreviver à recriação de variantes.

Apagar uma linha de atributo faz o Odoo destruir e recriar as variantes do artigo,
com identificadores novos. Antes da correção, os `product.document` continuavam a
apontar para o identificador antigo e ficavam presos a um registo inexistente — foi
assim que se acumularam 5697 documentos órfãos em produção, espalhados por 1790
variantes mortas.

Estes testes existem para que isso não volte a passar despercebido: o defeito era
silencioso, não dava erro nenhum, e só se via contando registos meses depois.
"""

import base64

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDocumentosSobrevivemAVariantes(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.updater = cls.env["product.update"]
        cls.atributo = cls.env["product.attribute"].create({
            "name": "Tensão de ensaio",
            "create_variant": "always",
        })
        cls.valores = cls.env["product.attribute.value"].create([
            {"name": "12V", "attribute_id": cls.atributo.id},
            {"name": "24V", "attribute_id": cls.atributo.id},
        ])
        cls.artigo = cls.env["product.template"].create({"name": "Fonte de ensaio"})

    def setUp(self):
        super().setUp()
        # Os documentos criados por cada teste, para as verificações se limitarem
        # a eles. Ver a nota em test_nenhum_documento_fica_orfao.
        self.criados = self.env["product.document"]

    def _anexar(self, variante, nome):
        doc = self.env["product.document"].create({
            "name": nome,
            "res_model": "product.product",
            "res_id": variante.id,
            # Conteúdo irrelevante: o que se testa é a ligação, não o ficheiro.
            "datas": base64.b64encode(b"ensaio"),
        })
        self.criados |= doc
        return doc

    def test_documento_segue_a_variante_pela_referencia(self):
        """Com referência interna, o documento acompanha a variante recriada."""
        self.updater._ensure_attribute_line(
            self.artigo, self.atributo, self.valores[0].ids)
        variante = self.artigo.product_variant_ids[:1]
        variante.default_code = "ENS-12V"
        doc = self._anexar(variante, "ficha.pdf")
        id_antigo = variante.id

        # Alterar o conjunto de valores obriga o Odoo a recriar as combinações.
        self.updater._ensure_attribute_line(
            self.artigo, self.atributo, self.valores.ids, prune_stale=True)

        self.assertTrue(doc.exists(), "O documento não pode desaparecer.")
        self.assertEqual(doc.res_model, "product.product")
        nova = self.env["product.product"].browse(doc.res_id)
        self.assertTrue(nova.exists(), "O documento ficou preso a uma variante morta.")
        self.assertEqual(nova.default_code, "ENS-12V",
                         "Devia ter seguido a variante com a mesma referência.")
        if nova.id != id_antigo:
            self.assertNotIn(id_antigo, self.artigo.product_variant_ids.ids)

    def test_documento_sem_referencia_passa_para_o_artigo(self):
        """Sem referência não há ponte possível — o documento sobe ao artigo-pai.

        Perde-se a especificidade da variante, mas o ficheiro continua alcançável.
        Ficar órfão tornava-o ilegível até por API.
        """
        self.updater._ensure_attribute_line(
            self.artigo, self.atributo, self.valores[0].ids)
        variante = self.artigo.product_variant_ids[:1]
        variante.default_code = False
        doc = self._anexar(variante, "desenho.dxf")

        self.updater._ensure_attribute_line(
            self.artigo, self.atributo, self.valores.ids, prune_stale=True)

        self.assertTrue(doc.exists())
        if doc.res_model == "product.product":
            alvo = self.env["product.product"].browse(doc.res_id)
            self.assertTrue(alvo.exists(),
                            "Documento sem referência ficou preso a uma variante morta.")
        else:
            self.assertEqual(doc.res_model, "product.template")
            self.assertEqual(doc.res_id, self.artigo.id)

    def test_nenhum_documento_fica_orfao(self):
        """A garantia que interessa: depois da operação, zero órfãos."""
        self.updater._ensure_attribute_line(
            self.artigo, self.atributo, self.valores[0].ids)
        for indice, variante in enumerate(self.artigo.product_variant_ids):
            variante.default_code = "ENS-%03d" % indice
            self._anexar(variante, "doc-%03d.pdf" % indice)

        self.updater._ensure_attribute_line(
            self.artigo, self.atributo, self.valores.ids, prune_stale=True)

        # Verificar SO os documentos criados por este teste. A primeira versão
        # procurava em toda a base e falhava sempre: as bases de teste do Odoo.sh
        # são restauradas da produção, que arrasta 5697 órfãos históricos — os
        # mesmos que esta correção existe para impedir daqui para a frente, mas
        # que ela não apaga.
        mortos = [d for d in self.criados
                  if d.exists() and d.res_model == "product.product"
                  and not self.env["product.product"].browse(d.res_id).exists()]
        self.assertFalse(
            mortos,
            "Ficaram %d documentos deste teste presos a variantes inexistentes."
            % len(mortos))
