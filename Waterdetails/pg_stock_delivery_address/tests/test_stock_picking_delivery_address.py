from odoo.tests import common, tagged


@tagged("post_install", "-at_install", "pg_stock_delivery_address")
class TestStockPickingDeliveryAddress(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_1 = cls.env["res.company"].create({"name": "Test Company 1"})
        cls.company_2 = cls.env["res.company"].create({"name": "Test Company 2"})
        cls.partner = cls.env["res.partner"].create({
            "name": "Test Main Partner",
            "is_company": True,
            "company_id": False,
        })
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        cls.picking_type = cls.warehouse.out_type_id or cls.env["stock.picking.type"].search([
            ("code", "=", "outgoing"),
            ("warehouse_id.company_id", "=", cls.env.company.id),
        ], limit=1)

    def test_sync_delivery_address_creates_global_partner(self):
        picking = self.env["stock.picking"].create({
            "partner_id": self.partner.id,
            "picking_type_id": self.picking_type.id,
            "location_id": self.picking_type.default_location_src_id.id,
            "location_dest_id": self.partner.property_stock_customer.id,
            "pg_delivery_street": "Rua Principal 123",
            "pg_delivery_city": "Lisboa",
            "pg_delivery_zip": "1000-001",
        })
        created_address = picking.pg_delivery_address_id
        self.assertTrue(created_address, "A delivery address should have been created")
        self.assertFalse(created_address.company_id, "Delivery address company_id must be False (global)")
        self.assertEqual(created_address.parent_id, self.partner, "Parent must be the main partner")
        self.assertTrue(created_address.pg_picking_delivery_address)
        self.assertEqual(created_address.type, "delivery")

    def test_sync_delivery_address_with_child_partner_keeps_root_parent(self):
        child_partner = self.env["res.partner"].create({
            "name": "Child Contact",
            "parent_id": self.partner.id,
            "type": "delivery",
            "company_id": False,
        })
        picking = self.env["stock.picking"].create({
            "partner_id": child_partner.id,
            "picking_type_id": self.picking_type.id,
            "location_id": self.picking_type.default_location_src_id.id,
            "location_dest_id": self.partner.property_stock_customer.id,
            "pg_delivery_street": "Nova Rua 456",
            "pg_delivery_city": "Porto",
            "pg_delivery_zip": "4000-001",
        })
        created_address = picking.pg_delivery_address_id
        self.assertTrue(created_address)
        self.assertFalse(created_address.company_id)
        self.assertEqual(created_address.parent_id, self.partner, "Parent must be the root commercial partner, not the child")
