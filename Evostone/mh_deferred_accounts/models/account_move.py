from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_deferred_account_for_line(self, line, deferred_type):
        """Devolve a conta de diferimento para uma linha, priorizando a conta
        específica do produto sobre a default da empresa."""
        product = line.product_id
        if product:
            product = product.with_company(self.company_id)
            if deferred_type == "expense" and product.deferred_expense_account_id:
                return product.deferred_expense_account_id
            if deferred_type == "revenue" and product.deferred_revenue_account_id:
                return product.deferred_revenue_account_id
        if deferred_type == "expense":
            return self.company_id.deferred_expense_account_id
        return self.company_id.deferred_revenue_account_id

    def _generate_deferred_entries(self):
        """Após a geração standard dos deferred moves, troca a conta default
        pela conta específica do produto (se definida)."""
        res = super()._generate_deferred_entries()
        if self.state != 'posted' or self.is_entry():
            return res

        deferred_type = "expense" if self.is_purchase_document() else "revenue"
        company_default = (
            self.company_id.deferred_expense_account_id
            if deferred_type == "expense"
            else self.company_id.deferred_revenue_account_id
        )
        if not company_default:
            return res

        # Por cada linha original com deferred + produto com conta específica,
        # localiza as linhas nos deferred moves (que preservam product_id) e troca a conta.
        for line in self.line_ids.filtered(
            lambda l: l.deferred_start_date and l.deferred_end_date and l.product_id
        ):
            specific_account = self._get_deferred_account_for_line(line, deferred_type)
            if not specific_account or specific_account == company_default:
                continue
            lines_to_update = self.deferred_move_ids.line_ids.filtered(
                lambda l2: l2.account_id == company_default
                and l2.product_id == line.product_id
            )
            if lines_to_update:
                lines_to_update.with_context(check_move_validity=False).write({
                    'account_id': specific_account.id,
                })
        return res
