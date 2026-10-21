# -*- coding: utf-8 -*-

import base64
import json
from odoo import models, fields, api, _
from importlib import import_module
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round
from odoo.exceptions import UserError
from odoo import _
import logging
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    is_jas_synced = fields.Boolean('Sincronizado c/ ERP')
    jas_invoice = fields.Binary('Documento PDF', attachment=False)
    doc_jasmin = fields.Char(string="Documento ERP")
    filename = fields.Char('Ficheiro')
    '''at_qr_code = fields.Text("AT QR Code", store=True)
    at_cud = fields.Char("AT CUD", store=True)
    legal_stamp = fields.Text("Legal Stamp", store=True)'''

    def add_jas_pdf_to_attachment(self, pdf_content, pdf_name):
        self.ensure_one()
        content = base64.encodebytes(pdf_content)
        attachment = self.env['ir.attachment'].create({
            'name': pdf_name,
            'datas': content,
            'store_fname': pdf_name,
            'res_model': self._name,
            'res_id': self.id,
            'res_name': self.name,
            'type': 'binary',
            'mimetype': 'application/pdf',
        })

        # Generate the URL to view the PDF
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        pdf_url = f"{base_url}/web/content/{attachment.id}?download=true"

        self.message_post(
            body="Jasmin PDF added in attachment.",
            attachment_ids=attachment.ids
        )

        self.write({          
            'jas_invoice': content,
            'filename': pdf_name
        })

        # Inject JavaScript into the client's browser to open the PDF
        action = {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {
                'url': pdf_url,
            },
        }

        return action

    def connect_jas_and_sync_invoice(self):

        conn = self._get_jas_connection()
        response = conn.authenticate()

        if response and response is True:
            self.is_jas_synced = False


            #fields = self.fields_get()
            #field_names = list(fields.keys())
            #_logger.error("self.field_names %s", field_names)

            #_logger.error("self.field_names %s %s %s %s", self.move_type, self.name, self.source_id, self.pos_order_ids)

            #raise UserError("ERROR")

            
            if self.journal_id.type == 'sale':

                company = self.company_id
                base_url = f'https://my.jasminsoftware.com/api/{company.jas_tenant_key}/{company.jas_org_key}'

                company = self.company_id
                pos = False
                if self.pos_order_ids:
                    pos = True
                    total_amount = sum(line.price_total for line in self.invoice_line_ids)
                    if total_amount > 100:
                        TipoDoc = company.jas_fr
                    else:
                        TipoDoc = company.jas_fs
                else:
                    TipoDoc = company.jas_ft

                if self.move_type != 'out_refund':
                    data, as_error, pdffile, docdata = conn.try_create_sale(move=self, TipoDocInvoice=TipoDoc)
                else:
                    data, as_error, pdffile, docdata = conn.try_create_refund(move=self, TipoDocInvoice=TipoDoc, pos=pos)
                #_logger.error(docdata)

                if not as_error:
                    if isinstance(data, dict):
                        if data['ErrorMessage'] != "":
                            response = "dict: " + data['ErrorMessage']
                            raise ValidationError(_(str(response)))

                    document_type = docdata.get('documentType')
                    document_series = docdata.get('serie')
                    document_number = docdata.get('seriesNumber')
                    document_SAFT = docdata.get('naturalKey')
                    
                    # Extract information from docdata
                    #self.legal_stamp = docdata.get('legalStamp')
                    #self.at_cud = docdata.get('aTCUD')
                    #self.at_qr_code = docdata.get('aTQRCode')
                    '''self.document_type_description = docdata.get('documentTypeDescription')
                    self.natural_key = docdata.get('naturalKey')'''
                    

                    
                    # Assuming there is a related POS order for this move
                    '''pos_order = self.env['pos.order'].search([('account_move', '=', self.id)], limit=1)
                    
                    if pos_order:
                        pos_order.write({
                            'legal_stamp': self.legal_stamp,
                            'at_cud': self.at_cud,
                            'at_qr_code': self.at_qr_code,
                        })'''
                        
                    self.is_jas_synced = True
                    self.doc_jasmin = document_SAFT
                    self.message_post(body=document_SAFT)
                    self.add_jas_pdf_to_attachment(pdffile,f"{document_type} {document_series}/{document_number}.pdf")

                else:
                    raise ValidationError(_("Erro: " + str(data)) + str(as_error))
        else:
            self.is_jas_synced = False

    def action_sync_to_erp(self):
        self.ensure_one()
        self.connect_jas_and_sync_invoice()

    def _post(self, soft=True):

        moves = super(AccountMove, self)._post(soft)

        for move in moves:
            #_logger.info("move.journal_id.type %s", move.journal_id.type)
            if move.journal_id.type == 'sale':
               move = self.env['account.move'].browse(moves.id)
               move.connect_jas_and_sync_invoice()
              

        return moves


    @staticmethod
    def pre_validation(company):
        err_msg = ''
        if not company.jas_company:
            err_msg += '\n Empresa'
        if not company.jas_username:
            err_msg += '\n Utilizador'
        if not company.jas_password:
            err_msg += '\n Password'
        if not company.jas_tenant_key:
            err_msg += '\n Chave'
        if not company.jas_org_key:
            err_msg += '\n Chave organização'
        if not company.jas_ft:
            err_msg += '\n Fatura'
        if not company.jas_fs:
            err_msg += '\n Fatura simplificada'
        if not company.jas_fr:
            err_msg += '\n Fatura recibo'
        if err_msg:
            err_msg = 'Configure as definições: ' + err_msg
            raise ValidationError(_(err_msg))

    def _get_jas_connection(self):
        self.ensure_one()

        company = self.company_id
        self.pre_validation(company)
        connector = import_module(
            'odoo.addons.pg_jasmin_integration.models.jas_connection')
        return (getattr(connector, 'JASConnection') (
                url='https://my.jasminsoftware.com/api',
                company=company.jas_company,
                username=company.jas_username,
                password=company.jas_password,
                tenant_key=company.jas_tenant_key,
                org_key=company.jas_org_key,
                fatura=company.jas_ft, 
                faturaRecibo=company.jas_fr,
                faturasimplificada=company.jas_fs, 
            )
        )


