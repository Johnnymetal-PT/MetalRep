# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestExemptAttrs(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Attr = cls.env['product.attribute']
        cls.wood = Attr.create({'name': 'CAT MADEIRA T', 'create_variant': 'always',
                                'value_ids': [(0, 0, {'name': 'W1'})]})
        cls.fabric = Attr.create({'name': 'CAT TECIDO T', 'create_variant': 'always',
                                  'value_ids': [(0, 0, {'name': 'F1'})]})
        cls.tmpl = cls.env['product.template'].create({
            'name': 'Produto teste', 'list_price': 1000.0,
            'attribute_line_ids': [
                (0, 0, {'attribute_id': cls.wood.id, 'value_ids': [(6, 0, cls.wood.value_ids.ids)]}),
                (0, 0, {'attribute_id': cls.fabric.id, 'value_ids': [(6, 0, cls.fabric.value_ids.ids)]}),
            ],
        })
        for ptav in cls.tmpl.attribute_line_ids.product_template_value_ids:
            ptav.price_extra = 200.0 if ptav.attribute_id == cls.wood else 100.0
        cls.product = cls.tmpl.product_variant_ids[:1]
        cls.pricelist = cls.env['product.pricelist'].create({
            'name': 'NET teste',
            'item_ids': [(0, 0, {
                'applied_on': '3_global', 'compute_price': 'formula',
                'base': 'list_price', 'price_discount': -25.0,
            })],
        })

    def _price(self, pricelist=None):
        return (pricelist or self.pricelist)._get_product_price(self.product, 1.0)

    def test_standard_sem_isencao(self):
        # (1000 + 200 + 100) x 1,25
        self.assertAlmostEqual(self.product.lst_price, 1300.0)
        self.assertAlmostEqual(self._price(), 1625.0, places=2)

    def test_isencao_do_tecido(self):
        self.pricelist.pg_exempt_attribute_ids = self.fabric
        # (1000 + 200) x 1,25 + 100
        self.assertAlmostEqual(self._price(), 1600.0, places=2)

    def test_isencao_de_todos_os_atributos(self):
        self.pricelist.pg_exempt_attribute_ids = self.fabric | self.wood
        # 1000 x 1,25 + 200 + 100
        self.assertAlmostEqual(self._price(), 1550.0, places=2)

    def test_desconto_normal_continua_a_funcionar(self):
        self.pricelist.item_ids.price_discount = 10.0
        self.pricelist.pg_exempt_attribute_ids = self.fabric
        # (1000 + 200) x 0,90 + 100
        self.assertAlmostEqual(self._price(), 1180.0, places=2)

    def test_lista_sem_isencao_nao_muda(self):
        outra = self.pricelist.copy({'name': 'Outra'})
        self.assertAlmostEqual(self._price(outra), 1625.0, places=2)
