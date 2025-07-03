from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class AgedPartnerBalanceCustomHandlerExtension(models.AbstractModel):
    _inherit = 'account.aged.partner.balance.report.handler'

    def _aged_partner_report_custom_engine_common(
        self, options, internal_type, current_groupby, next_groupby, offset=0, limit=None
    ):
        results = super()._aged_partner_report_custom_engine_common(
            options, internal_type, current_groupby, next_groupby, offset, limit
        )

        def compute_days_overdue(invoice_date):
            if invoice_date:
                if isinstance(invoice_date, str):
                    invoice_date = fields.Date.from_string(invoice_date)
                return (fields.Date.today() - invoice_date).days
            return None

        def add_days_overdue_to_result(res_dict):
            invoice_date = res_dict.get('invoice_date')
            res_dict['days_overdue'] = compute_days_overdue(invoice_date)

        if not current_groupby:
            add_days_overdue_to_result(results)
            _logger.info("✅ Final Summary Result: %s", results)
        else:
            for index, result in enumerate(results):
                grouping_key, res_dict = result
                add_days_overdue_to_result(res_dict)
                _logger.info("✅ Final Grouped Result [%s]: %s", grouping_key, res_dict)

        return results

    def _prepare_partner_values(self):
        return {
            'invoice_date': None,
            'due_date': None,
            'amount_currency': None,
            'currency_id': None,
            'currency': None,
            'account_name': None,
            'expected_date': None,
            'total': 0,
            'days_overdue': None,  # ✅ Added to prevent KeyError
        }
