# Copyright 2025 MH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestMultipleDiscount(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.groups_id += cls.env.ref("product.group_discount_per_so_line")

        cls.product = cls.env["product.product"].create({
            "name": "Test Product",
            "type": "consu",
            "list_price": 100.0,
        })

        cls.partner = cls.env["res.partner"].create({
            "name": "Test Customer",
        })

    def test_01_multiplicative_discount_sale(self):
        """Test multiplicative discount calculation on sale order"""
        order = self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "order_line": [(0, 0, {
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 100.0,
                "discount": 30.0,
                "discount2": 20.0,
                "discount3": 10.0,
                "discount4": 5.0,
                "discounting_type": "multiplicative",
            })],
        })

        line = order.order_line[0]
        # Multiplicative: (1-0.30) * (1-0.20) * (1-0.10) * (1-0.05) = 0.4788
        # Price: 100 * 0.4788 = 47.88
        self.assertAlmostEqual(line.price_subtotal, 47.88, places=2)

    def test_02_additive_discount_sale(self):
        """Test additive discount calculation on sale order"""
        order = self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "order_line": [(0, 0, {
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 100.0,
                "discount": 30.0,
                "discount2": 20.0,
                "discount3": 10.0,
                "discount4": 5.0,
                "discounting_type": "additive",
            })],
        })

        line = order.order_line[0]
        # Additive: 30 + 20 + 10 + 5 = 65%
        # Price: 100 * (1 - 0.65) = 35.00
        self.assertAlmostEqual(line.price_subtotal, 35.0, places=2)

    def test_03_transfer_to_invoice(self):
        """Test that all discount fields are transferred to invoice"""
        order = self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "order_line": [(0, 0, {
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 100.0,
                "discount": 30.0,
                "discount2": 20.0,
                "discount3": 10.0,
                "discount4": 5.0,
                "discounting_type": "additive",
            })],
        })

        order.action_confirm()
        invoice = order._create_invoices()

        sale_line = order.order_line[0]
        invoice_line = invoice.invoice_line_ids[0]

        # Check all fields are transferred
        self.assertEqual(sale_line.discount, invoice_line.discount)
        self.assertEqual(sale_line.discount2, invoice_line.discount2)
        self.assertEqual(sale_line.discount3, invoice_line.discount3)
        self.assertEqual(sale_line.discount4, invoice_line.discount4)
        self.assertEqual(sale_line.discounting_type, invoice_line.discounting_type)

        # Check price is consistent
        self.assertAlmostEqual(sale_line.price_subtotal, invoice_line.price_subtotal, places=2)

    def test_04_multiplicative_discount_invoice(self):
        """Test multiplicative discount calculation on invoice"""
        invoice = self.env["account.move"].create({
            "partner_id": self.partner.id,
            "move_type": "out_invoice",
            "invoice_line_ids": [(0, 0, {
                "product_id": self.product.id,
                "quantity": 1,
                "price_unit": 100.0,
                "discount": 30.0,
                "discount2": 20.0,
                "discount3": 10.0,
                "discount4": 5.0,
                "discounting_type": "multiplicative",
            })],
        })

        line = invoice.invoice_line_ids[0]
        # Multiplicative: (1-0.30) * (1-0.20) * (1-0.10) * (1-0.05) = 0.4788
        # Price: 100 * 0.4788 = 47.88
        self.assertAlmostEqual(line.price_subtotal, 47.88, places=2)

    def test_05_additive_discount_invoice(self):
        """Test additive discount calculation on invoice"""
        invoice = self.env["account.move"].create({
            "partner_id": self.partner.id,
            "move_type": "out_invoice",
            "invoice_line_ids": [(0, 0, {
                "product_id": self.product.id,
                "quantity": 1,
                "price_unit": 100.0,
                "discount": 30.0,
                "discount2": 20.0,
                "discount3": 10.0,
                "discount4": 5.0,
                "discounting_type": "additive",
            })],
        })

        line = invoice.invoice_line_ids[0]
        # Additive: 30 + 20 + 10 + 5 = 65%
        # Price: 100 * (1 - 0.65) = 35.00
        self.assertAlmostEqual(line.price_subtotal, 35.0, places=2)

    def test_06_additive_cap_at_100(self):
        """Test that additive discount is capped at 100%"""
        order = self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "order_line": [(0, 0, {
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 100.0,
                "discount": 50.0,
                "discount2": 40.0,
                "discount3": 30.0,
                "discount4": 20.0,
                "discounting_type": "additive",
            })],
        })

        line = order.order_line[0]
        # Additive: 50 + 40 + 30 + 20 = 140% → capped at 100%
        # Price: 100 * (1 - 1.0) = 0.00
        self.assertAlmostEqual(line.price_subtotal, 0.0, places=2)
