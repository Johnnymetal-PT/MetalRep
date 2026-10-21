# Copyright 2013-17 Agile Business Group (<http://www.agilebg.com>)
# Copyright 2016 AvanzOSC (<http://www.avanzosc.es>)
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import common, tagged


@tagged("post_install", "-at_install")
class TestSaleStockPickingInvoiceLink(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Customer"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "is_storable": True,
                "invoice_policy": "delivery",
            }
        )
        cls.order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "product_uom_qty": 2.0,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )

    def test_invoice_picking_link(self):
        self.order.action_confirm()
        picking = self.order.picking_ids
        self.assertTrue(picking)
        for move in picking.move_ids:
            move.quantity = 2.0
        picking.button_validate()
        self.assertEqual(picking.state, "done")

        # Create invoice
        invoice = self.order._create_invoices()
        self.assertTrue(invoice)
        self.assertIn(picking, invoice.picking_ids)
        self.assertIn(invoice, picking.invoice_ids)
