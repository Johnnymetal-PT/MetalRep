from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestSelectiveEarlyDiscount(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.early_payment_term = cls.env["account.payment.term"].create({
            "name": "10% P.P. em 10 dias",
            "company_id": cls.company_data["company"].id,
            "early_discount": True,
            "discount_percentage": 10.0,
            "discount_days": 10,
            "line_ids": [Command.create({
                "value": "percent",
                "value_amount": 100.0,
                "nb_days": 30,
            })],
        })

    def _create_invoice(self, tax=None):
        tax_ids = [Command.set(tax.ids)] if tax else []
        return self.env["account.move"].create({
            "move_type": "in_invoice",
            "partner_id": self.partner_a.id,
            "invoice_date": "2026-08-03",
            "date": "2026-08-03",
            "invoice_payment_term_id": self.early_payment_term.id,
            "invoice_line_ids": [
                Command.create({
                    "name": "Mercadoria",
                    "price_unit": 100.0,
                    "quantity": 1.0,
                    "tax_ids": tax_ids,
                    "pg_early_discount_eligible": True,
                }),
                Command.create({
                    "name": "Portes",
                    "price_unit": 15.0,
                    "quantity": 1.0,
                    "tax_ids": tax_ids,
                    "pg_early_discount_eligible": False,
                }),
            ],
        })

    def test_only_selected_lines_reduce_amount_due(self):
        invoice = self._create_invoice()
        payment_term_line = invoice.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        )

        self.assertRecordValues(invoice, [{
            "amount_total": 115.0,
            "pg_early_discount_amount": 10.0,
            "pg_amount_after_early_discount": 105.0,
        }])
        self.assertEqual(abs(payment_term_line.discount_amount_currency), 105.0)

        invoice.invoice_line_ids.filtered(
            lambda line: line.name == "Portes"
        ).pg_early_discount_eligible = True
        self.assertEqual(invoice.pg_early_discount_amount, 11.5)
        self.assertEqual(
            abs(payment_term_line.discount_amount_currency), 103.5
        )

    def test_amount_due_reflects_early_discount_until_first_payment(self):
        invoice = self._create_invoice()
        invoice.action_post()

        # Nada reconciliado: o valor em dívida é o total menos o desconto p.p.
        self.assertRecordValues(invoice, [{
            "amount_residual": 115.0,
            "pg_amount_residual_after_early_discount": 105.0,
            "amount_residual_signed": -115.0,
            "pg_amount_residual_signed_after_early_discount": -105.0,
        }])

        # A partir do primeiro movimento reconciliado vale o valor em dívida
        # contabilístico: o desconto está realizado (ou perdido) nos lançamentos.
        self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=invoice.ids
        ).create({"payment_date": invoice.invoice_date})._create_payments()

        self.assertEqual(
            invoice.pg_amount_residual_after_early_discount,
            invoice.amount_residual,
        )
        self.assertEqual(
            invoice.pg_amount_residual_signed_after_early_discount,
            invoice.amount_residual_signed,
        )

    def test_bank_rec_list_shows_discounted_amount_due(self):
        invoice = self._create_invoice()
        invoice.action_post()
        payment_term_line = invoice.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        )

        # Valores lidos pelas colunas novas da reconciliação bancária: o valor
        # com desconto só se distingue do valor em dívida enquanto nada foi pago.
        self.assertEqual(payment_term_line.amount_residual_currency, -115.0)
        self.assertEqual(payment_term_line.amount_currency, -115.0)
        self.assertEqual(payment_term_line.discount_amount_currency, -105.0)
        self.assertTrue(payment_term_line.discount_date)

        view = self.env.ref(
            "account_accountant.view_account_move_line_list_bank_rec_widget"
        )
        arch = self.env["account.move.line"].get_view(view.id, "list")["arch"]
        self.assertIn("discount_amount_currency", arch)
        self.assertIn("discount_date", arch)

    def test_amount_due_untouched_without_early_discount(self):
        invoice = self._create_invoice()
        invoice.invoice_payment_term_id = False
        invoice.action_post()

        self.assertFalse(invoice.pg_has_early_discount)
        self.assertEqual(
            invoice.pg_amount_residual_after_early_discount,
            invoice.amount_residual,
        )
        self.assertEqual(
            invoice.pg_amount_residual_signed_after_early_discount,
            invoice.amount_residual_signed,
        )

    def test_tax_included_discount_counterpart_excludes_shipping(self):
        tax = self.env["account.tax"].create({
            "name": "IVA 23% teste P.P.",
            "amount": 23.0,
            "amount_type": "percent",
            "type_tax_use": "purchase",
            "company_id": self.company_data["company"].id,
        })
        invoice = self._create_invoice(tax=tax)

        self.assertEqual(invoice.amount_total, 141.45)
        self.assertEqual(invoice.pg_early_discount_amount, 12.3)
        self.assertEqual(invoice.pg_amount_after_early_discount, 129.15)

        invoice.action_post()
        counterpart_values = (
            invoice
            ._get_invoice_counterpart_amls_for_early_payment_discount_per_payment_term_line()
        )
        discount_amount = sum(
            values["amount_currency"]
            for category in counterpart_values.values()
            for values_per_term in category.values()
            for values in values_per_term.values()
        )
        self.assertEqual(abs(invoice.currency_id.round(discount_amount)), 12.3)

    def test_customer_invoice_early_discount(self):
        invoice = self.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": self.partner_a.id,
            "invoice_date": "2026-08-03",
            "date": "2026-08-03",
            "invoice_payment_term_id": self.early_payment_term.id,
            "invoice_line_ids": [
                Command.create({
                    "name": "Produto Cliente",
                    "price_unit": 200.0,
                    "quantity": 1.0,
                    "pg_early_discount_eligible": True,
                }),
            ],
        })
        self.assertTrue(invoice.pg_has_early_discount)
        self.assertEqual(invoice.amount_total, 200.0)
        self.assertEqual(invoice.pg_early_discount_amount, 20.0)
        self.assertEqual(invoice.pg_amount_after_early_discount, 180.0)

