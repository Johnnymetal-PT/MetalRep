from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestCustomerVatRequired(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_without_vat = cls.env["res.partner"].create({
            "name": "Cliente sem NIF",
            "vat": False,
        })
        cls.end_consumer = cls.env.ref("ptplus_partner.l10n_pt_end_consumer")

    def _create_move(self, move_type, partner):
        return self.env["account.move"].create({
            "move_type": move_type,
            "partner_id": partner.id,
            "invoice_date": "2026-10-20",
            "date": "2026-10-20",
            "invoice_line_ids": [Command.create({
                "name": "Mercadoria",
                "price_unit": 100.0,
                "quantity": 1.0,
                "tax_ids": [],
            })],
        })

    def test_customer_invoice_without_vat_cannot_be_posted(self):
        invoice = self._create_move("out_invoice", self.partner_without_vat)
        with self.assertRaises(UserError):
            invoice.action_post()
        self.assertEqual(invoice.state, "draft")

    def test_customer_credit_note_without_vat_cannot_be_posted(self):
        credit_note = self._create_move("out_refund", self.partner_without_vat)
        with self.assertRaises(UserError):
            credit_note.action_post()
        self.assertEqual(credit_note.state, "draft")

    def test_customer_invoice_with_vat_can_be_posted(self):
        self.partner_without_vat.vat = "PT503687081"
        invoice = self._create_move("out_invoice", self.partner_without_vat)
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")

    def test_end_consumer_without_vat_can_be_posted(self):
        invoice = self._create_move("out_invoice", self.end_consumer)
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")

    def test_vendor_bill_without_vat_can_be_posted(self):
        bill = self._create_move("in_invoice", self.partner_without_vat)
        bill.action_post()
        self.assertEqual(bill.state, "posted")
