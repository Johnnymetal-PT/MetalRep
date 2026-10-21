# -*- coding: utf-8 -*-
"""Ao enviar a fatura por email, usa o PDF oficial do PHC em vez do PDF gerado pelo Odoo.

Só atua quando a fatura já está sincronizada com o PHC (is_phc_synced). Ver o __manifest__.py.
"""
from odoo import models, api
import base64

class AccountMoveSend(models.TransientModel):
    _inherit = "account.move.send"

    def _get_placeholder_mail_attachments_data(self, move):
        res = super()._get_placeholder_mail_attachments_data(move)
        if res and move.is_phc_synced:
            filename = move.filename
            # Troca o placeholder do relatório Odoo pelo nome do PDF oficial PHC
            # para o utilizador ver o anexo correto antes do envio.
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
            # Substitui o binário do relatório standard pelo PDF devolvido pelo PHC.
            invoice_data["pdf_attachment_values"] = {
                "raw": base64.decodebytes(invoice.phc_invoice),
                "name": invoice.filename,
                "mimetype": "application/pdf",
                "res_model": invoice._name,
                "res_id": invoice.id,
                "res_field": "invoice_pdf_report_file",
            }
