# -*- coding: utf-8 -*-
"""Substitui o PDF do Odoo pelo PDF certificado JASMIN no email da fatura.

Quando o utilizador envia o email da fatura ao cliente, queremos que
o anexo seja o PDF certificado do JASMIN (com ATCUD, QR, etc.) em
vez do PDF interno do Odoo. Este wizard:
1. Substitui o placeholder do anexo pelo nome do ficheiro JASMIN.
2. Carrega os bytes do PDF JASMIN para ``pdf_attachment_values``
   antes do envio efetivo.

So aplica quando ``move.is_jas_synced`` esta True - faturas nao
sincronizadas mantem o comportamento Odoo standard.
"""
from odoo import models, api
import base64


class AccountMoveSend(models.TransientModel):
    _inherit = "account.move.send"

    def _get_placeholder_mail_attachments_data(self, move):
        res = super(AccountMoveSend, self)._get_placeholder_mail_attachments_data(move)
        # Substitui o placeholder do PDF Odoo pelo do PDF JASMIN.
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
        # Para faturas ja com PDF JASMIN, sobrescrever o raw do PDF
        # com os bytes descarregados em jas_invoice.
        if invoice.is_jas_synced:
            invoice_data['pdf_attachment_values'] = {
                'raw': base64.decodebytes(invoice.jas_invoice),
                'name': invoice.filename,
                'mimetype': 'application/pdf',
                'res_model': invoice._name,
                'res_id': invoice.id,
                # res_field para que o anexo fique ligado ao Binary
                # ``invoice_pdf_report_file`` (campo standard que o
                # Odoo serve no portal).
                'res_field': 'invoice_pdf_report_file',
            }
