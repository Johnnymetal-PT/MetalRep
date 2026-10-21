from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestStandardPurchaseFlow(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.po_double_validation = 'one_step'
        cls.category = cls.env['product.category'].create({
            'name': 'Test Standard AVCO',
            'property_cost_method': 'average',
            'property_valuation': 'manual_periodic',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Standard Purchase Product',
            'type': 'consu',
            'is_storable': True,
            'categ_id': cls.category.id,
            'product_classification': 'merchandise',
            'standard_price': 10.0,
        })
        cls.supplier = cls.env['res.partner'].create({
            'name': 'Test Standard Purchase Supplier',
            'supplier_rank': 1,
        })
        cls.service_type = cls.env['service.type'].create({
            'name': 'Test Standard Merchandise',
            'area_ids': [(6, 0, [cls.env.ref('mh_base.area_merchandise').id])],
        })

    def _create_purchase_order(self):
        return self.env['purchase.order'].create({
            'partner_id': self.supplier.id,
            'service_type_id': self.service_type.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.display_name,
                'product_qty': 2.0,
                'product_uom': self.product.uom_po_id.id,
                'price_unit': 12.0,
                'date_planned': '2026-09-30 10:00:00',
                'lot_name': 'TEST-STANDARD',
            })],
        })

    def test_confirm_uses_standard_flow_without_wizard(self):
        purchase_order = self._create_purchase_order()

        result = purchase_order.button_confirm()

        self.assertIs(result, True)
        self.assertEqual(purchase_order.state, 'purchase')
        self.assertTrue(purchase_order.picking_ids)

    def test_purchase_receipt_is_not_blocked_by_legacy_import_flag(self):
        purchase_order = self._create_purchase_order()
        purchase_order.button_confirm()
        purchase_order.no_cost_validation = False
        picking = purchase_order.picking_ids
        picking.action_assign()
        picking.move_ids.quantity = picking.move_ids.product_uom_qty

        picking.button_validate()

        self.assertEqual(picking.state, 'done')

    def test_average_cost_is_exposed_to_existing_pricing_fields(self):
        self.product.standard_price = 18.5
        self.product.invalidate_recordset(['pcmp'])

        self.assertEqual(self.product.pcmp, 18.5)

    def test_legacy_pcmp_cannot_be_selected(self):
        with self.assertRaises(ValidationError):
            self.category.property_cost_method = 'pcmp'
