from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class PartnerLedgerReportCustomHandlerExtension(models.AbstractModel):
    _inherit = 'account.partner.ledger.report.handler'

    def _custom_partner_ledger_report_engine(
        self, options, current_groupby, next_groupby, offset=0, limit=None
    ):
        results = super()._custom_partner_ledger_report_engine(
            options, current_groupby, next_groupby, offset, limit
        )

        def compute_days_overdue(invoice_date):
            if invoice_date:
                if isinstance(invoice_date, str):
                    invoice_date = fields.Date.from_string(invoice_date)
                return (fields.Date.today() - invoice_date).days
            return None

        def add_days_overdue(res_dict):
            invoice_date = res_dict.get('invoice_date')
            res_dict['days_overdue'] = compute_days_overdue(invoice_date)

        if not current_groupby:
            add_days_overdue(results)
            _logger.info("✅ Final Partner Ledger Summary Result: %s", results)
        else:
            for grouping_key, res_dict in results:
                add_days_overdue(res_dict)
                _logger.info("✅ Partner Ledger Grouped Result [%s]: %s", grouping_key, res_dict)

        return results

    def _prepare_partner_values(self):
        res = super()._prepare_partner_values()
        res['days_overdue'] = None  # ✅ Prevent KeyError
        return res

