# -*- coding: utf-8 -*-

from odoo import models, api
import base64

class AccountMoveSend(models.TransientModel):
    _inherit = "account.move.send"

    def _get_placeholder_mail_attachments_data(self, move):
        res = super(AccountMoveSend,self)._get_placeholder_mail_attachments_data(move)
        if res and move.is_jas_synced:
            filename = move.filename
            res = [{
                'id': f'placeholder_{filename}',
                'name': filename,
                'mimetype': 'application/pdf',
                'placeholder': True,
            }]
        return res

    @api.model
    def _prepare_invoice_pdf_report(self, invoice, invoice_data):
        super(AccountMoveSend, self)._prepare_invoice_pdf_report(
            invoice, invoice_data)
        if invoice.is_jas_synced:
            invoice_data['pdf_attachment_values'] = {
                'raw': base64.decodebytes(invoice.jas_invoice),
                'name': invoice.filename,
                'mimetype': 'application/pdf',
                'res_model': invoice._name,
                'res_id': invoice.id,
                'res_field': 'invoice_pdf_report_file',  # Binary field
            }
