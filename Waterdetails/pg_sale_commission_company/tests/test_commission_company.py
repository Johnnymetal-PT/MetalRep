import datetime

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestCommissionCompany(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.company_data["company"]
        cls.company_b = cls.company_data_2["company"]

        cls.salesperson = cls.env["res.users"].create({
            "name": "Vendedor Multiempresa",
            "login": "pg_vendedor_multiempresa",
            "company_id": cls.company_a.id,
            "company_ids": [Command.set((cls.company_a | cls.company_b).ids)],
            "group_ids": [Command.set(cls.env.ref("sales_team.group_sale_salesman").ids)],
        })

        cls.invoice_a = cls._create_salesperson_invoice(cls.company_a, 100.0)
        cls.invoice_b = cls._create_salesperson_invoice(cls.company_b, 300.0)

    @classmethod
    def _create_salesperson_invoice(cls, company, amount):
        invoice = cls.env["account.move"].with_company(company).create({
            "move_type": "out_invoice",
            "partner_id": cls.partner_a.id,
            "invoice_date": "2026-03-10",
            "invoice_user_id": cls.salesperson.id,
            "invoice_line_ids": [Command.create({
                "name": "Linha de teste",
                "quantity": 1,
                "price_unit": amount,
                "tax_ids": [Command.clear()],
            })],
        })
        invoice.action_post()
        return invoice

    def _create_plan(self, company):
        plan = self.env["sale.commission.plan"].create({
            "name": "Plano %s" % company.name,
            "company_id": company.id,
            "date_from": datetime.date(2026, 1, 1),
            "date_to": datetime.date(2026, 12, 31),
            "periodicity": "month",
            "type": "achieve",
            "user_type": "person",
        })
        # o plano já nasce com uma regra `amount_invoiced` por defeito
        plan.user_ids = self.env["sale.commission.plan.user"].create({
            "plan_id": plan.id,
            "user_id": self.salesperson.id,
            "date_from": datetime.date(2026, 1, 1),
        })
        plan.action_approve()
        return plan

    def _achieved_invoices(self, plan):
        report = self.env["sale.commission.achievement.report"]
        report._pre_achievement_operation()
        lines = report.search([
            ("plan_id", "=", plan.id),
            ("related_res_model", "=", "account.move"),
        ])
        return {line.related_res_id for line in lines}

    def test_plan_only_counts_invoices_of_its_own_company(self):
        plan_a = self._create_plan(self.company_a)
        self.assertEqual(
            self._achieved_invoices(plan_a),
            {self.invoice_a.id},
            "O plano da empresa A não pode contar faturas da empresa B.",
        )

    def test_plan_of_other_company_counts_only_its_own_invoices(self):
        plan_b = self._create_plan(self.company_b)
        self.assertEqual(
            self._achieved_invoices(plan_b),
            {self.invoice_b.id},
            "O plano da empresa B só deve contar faturas da empresa B.",
        )
