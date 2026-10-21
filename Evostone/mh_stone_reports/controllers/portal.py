from odoo.addons.account.controllers.portal import PortalAccount
from odoo.exceptions import AccessError, MissingError
from odoo import http
from odoo.http import request


# Mapeamento de move_type para report Stone
STONE_REPORT_MAP = {
    'out_invoice': 'mh_stone_reports.report_invoice',
    'out_refund': 'mh_stone_reports.report_credit_note',
    'in_refund': 'mh_stone_reports.report_debit_note',
    'in_invoice': 'mh_stone_reports.report_debit_note',
}


class PortalAccountStone(PortalAccount):

    @http.route()
    def portal_my_invoice_detail(self, invoice_id, access_token=None, report_type=None, download=False, **kw):
        try:
            invoice_sudo = self._document_check_access('account.move', invoice_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text') and not (report_type == 'pdf' and download and invoice_sudo.state == 'posted'):
            has_generated_invoice = bool(invoice_sudo.invoice_pdf_report_id)
            request.update_context(proforma_invoice=not has_generated_invoice)
            # Usar report Stone consoante o move_type
            pdf_report_name = STONE_REPORT_MAP.get(invoice_sudo.move_type)
            if not pdf_report_name:
                pdf_report_name = invoice_sudo.partner_id.invoice_template_pdf_report_id.report_name or 'account.account_invoices'
            return self._show_report(model=invoice_sudo, report_type=report_type, report_ref=pdf_report_name, download=download)

        return super().portal_my_invoice_detail(invoice_id, access_token=access_token, report_type=report_type, download=download, **kw)
