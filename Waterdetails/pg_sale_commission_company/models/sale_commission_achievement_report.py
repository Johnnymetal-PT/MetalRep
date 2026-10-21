from odoo import api, models


class SaleCommissionAchievementReport(models.Model):
    _inherit = "sale.commission.achievement.report"

    # O standard liga as faturas e encomendas ao plano apenas pelo vendedor
    # (ver `_join_invoices` / `_join_sales`), sem olhar à empresa. Um vendedor
    # com plano na empresa A acumulava assim também documentos da empresa B.
    # Os dois hooks abaixo são anexados à cláusula WHERE da query SQL do
    # relatório, onde `rules` é a regra do plano (com a empresa do plano),
    # `fm` a fatura e `fo` a encomenda.

    @api.model
    def _where_invoices(self):
        res = super()._where_invoices()
        res += """
          AND fm.company_id = rules.company_id
        """
        return res

    @api.model
    def _where_sales(self):
        res = super()._where_sales()
        res += """
          AND fo.company_id = rules.company_id
        """
        return res
