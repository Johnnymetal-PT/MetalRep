from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)

class PartnerLedgerCustomHandler(models.AbstractModel):
    _inherit = 'account.partner.ledger.report.handler'

    def _custom_engine_partner_ledger_report(self, options, current_groupby, next_groupby, offset=0, limit=None):
        results = super()._custom_engine_partner_ledger_report(options, current_groupby, next_groupby, offset, limit)

        def compute_days_overdue(due_date):
            if due_date:
                if isinstance(due_date, str):
                    due_date = fields.Date.from_string(due_date)
                return (fields.Date.today() - due_date).days
            return None

        def add_days_overdue_to_result(res_dict):
            due_date = res_dict.get('due_date')
            res_dict['days_overdue'] = compute_days_overdue(due_date)

        if not current_groupby:
            add_days_overdue_to_result(results)
            _logger.info("✅ Partner Ledger Summary Result: %s", results)
        else:
            for _, res_dict in results:
                add_days_overdue_to_result(res_dict)
                _logger.info("✅ Partner Ledger Grouped Result: %s", res_dict)

        return results

    def _prepare_partner_values(self):
        res = super()._prepare_partner_values()
        res['days_overdue'] = None
        return res

