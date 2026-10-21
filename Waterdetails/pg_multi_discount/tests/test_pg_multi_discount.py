from odoo.fields import Command
from odoo.tests import common, tagged


@tagged("post_install", "-at_install")
class TestPgMultiDiscount(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({
            "name": "PG Multi Discount Partner",
        })
        cls.product = cls.env["product.product"].create({
            "name": "PG Multi Discount Service",
            "type": "service",
            "list_price": 141.5,
        })

    def test_manual_invoice_line_keeps_unit_total_without_multi_discount(self):
        invoice = self.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": self.partner.id,
            "invoice_line_ids": [
                Command.create({
                    "product_id": self.product.id,
                    "name": self.product.name,
                    "quantity": 1.0,
                    "price_unit": 141.5,
                }),
            ],
        })

        line = invoice.invoice_line_ids
        self.assertFalse(line.sh_multi_discount)
        self.assertEqual(line.sh_discount_amount, 0.0)
        self.assertEqual(line.sh_discounted_total_amount, 0.0)
        self.assertEqual(line.sh_discount_price_unit, 141.5)
