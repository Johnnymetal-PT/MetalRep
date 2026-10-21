# -*- coding: utf-8 -*-
"""
Wizard legacy de envio de faturas para PHC.

Modulo: pg_phc_api_integration_old.
Ficheiro: pg_phc_api_integration_old/wizard/account_move_send.py.
Estende account.move.send com operacoes especificas de integracao.
"""

from odoo import models, api
import base64

class AccountMoveSend(models.TransientModel):  # <-- IMPORTANT CHANGE
    _inherit = "account.move.send"

    def _get_placeholder_mail_attachments_data(self, move):
        res = super()._get_placeholder_mail_attachments_data(move)
        if res and move.is_phc_synced:
            filename = move.filename
            # Troca o placeholder do relatório Odoo pelo nome do PDF oficial PHC.
            res = [{
                "id": f"placeholder_{filename}",
                "name": filename,
                "mimetype": "application/pdf",
                "placeholder": True,
            }]
        return res

    @api.model
    def _prepare_invoice_pdf_report(self, invoice, invoice_data):
        super()._prepare_invoice_pdf_report(invoice, invoice_data)
        if invoice.is_phc_synced:
            # No envio por email, força o anexo a usar o PDF recebido do PHC.
            invoice_data["pdf_attachment_values"] = {
                "raw": base64.decodebytes(invoice.phc_invoice),
                "name": invoice.filename,
                "mimetype": "application/pdf",
                "res_model": invoice._name,
                "res_id": invoice.id,
                "res_field": "invoice_pdf_report_file",
            }

