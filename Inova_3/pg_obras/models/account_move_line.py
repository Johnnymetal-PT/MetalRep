from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        if not self._context.get("skip_auto_account"):
            lines._apply_vendor_bill_account_rules()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if self._context.get("skip_auto_account"):
            return res
        self._apply_vendor_bill_account_rules()
        return res

    def _apply_vendor_bill_account_rules(self):
        """Atualiza a conta consoante a distribuição analítica em faturas de fornecedor."""
        lines = self.filtered(
            lambda l: l.move_id
            and l.move_id.move_type == "in_invoice"
            and l.move_id.state == "draft"
            and not l.display_type
        )
        if not lines:
            return

        accounts_by_company = {}
        for company in lines.mapped("company_id"):
            accounts_by_company[company.id] = {
                "with_distribution": self.env["account.account"].search(
                    [("code", "=", "361000"), ("company_id", "in", [company.id, False])],
                    limit=1,
                ),
                "without_distribution": self.env["account.account"].search(
                    [("code", "=", "311000"), ("company_id", "in", [company.id, False])],
                    limit=1,
                ),
            }

        for line in lines:
            company_accounts = accounts_by_company.get(line.company_id.id, {})
            target_account = (
                company_accounts.get("with_distribution")
                if line.analytic_distribution
                else company_accounts.get("without_distribution")
            )

            if target_account and line.account_id != target_account:
                line.with_context(skip_auto_account=True).write(
                    {"account_id": target_account.id}
                )
