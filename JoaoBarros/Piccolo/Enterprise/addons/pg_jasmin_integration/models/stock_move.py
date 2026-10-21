import base64
import logging
from odoo import models, fields, _
from odoo.exceptions import ValidationError
from .jas_connection import JASConnection  # Import the JASConnection class
import requests

_logger = logging.getLogger(__name__)

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_jasmin_connection(self):
        """
        Create and return a JASConnection instance.
        """
        company = self.company_id

        # Fetch credentials from the company record
        jasmin_connection = JASConnection(
            url='https://my.jasminsoftware.com/api',
            company=company.id,
            username=company.jas_username,
            password=company.jas_password,
            tenant_key=company.jas_tenant_key,
            org_key=company.jas_org_key,
            fatura='FT',
            faturaRecibo='FR',
            faturasimplificada='FS',
        )

        if not jasmin_connection.access_token:
            raise ValidationError(_("Failed to authenticate with Jasmim API. Please check your credentials."))

        return jasmin_connection

    def send_to_jasmim(self, picking):
        """
        Send the document data to Jasmim GT and fetch the response.
        """
        jasmin_connection = self._get_jasmin_connection()  # Reuse JASConnection
        doc_data = self.prepare_delivery_payload(picking, jasmin_connection.company)

        headers = {
            "Authorization": f"Bearer {jasmin_connection.access_token}",
            "Content-Type": "application/json",
        }

        api_url = f"{jasmin_connection.work_url}/shipping/deliveries"

        try:
            response = requests.post(api_url, json=doc_data, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            _logger.error("Error sending document to Jasmim: %s", str(e))
            raise ValidationError(_("Failed to communicate with Jasmim API: %s") % str(e))

    def prepare_delivery_payload(self, picking, jas_company):

        partner = picking.partner_id
        address = partner.contact_address

        doc_data = {
            "company": "PICCOLO", #jas_company,
            "Party": partner.id,
            "documentType": "GT",
            "printedReportName": "SHIPPING_DELIVERYREPORT_DEFAULT",
            "deliveryTerm": "TRANSP",
            #"documentDate": fields.Date.context_today(self),
            "logisticPartyAddress": address,
            #"loadingDateTime": picking.scheduled_date.strftime("%Y-%m-%dT%H:%M:%S"),
            #"unloadingDateTime": picking.date_done.strftime("%Y-%m-%dT%H:%M:%S") if picking.date_done else "",
            "unloadingStreetName": partner.street or "",
            "unloadingPostalZone": partner.zip or "",
            "unloadingCityName": partner.city or "",
            #"vehiclePlateNumber": picking.car_plate or "UNKNOWN",
            #"aTDocCodeID": picking.origin or "12345678",
            "documentLines": [],
        }

        # Loop through stock moves and prepare document lines
        for moves in picking.move_ids_without_package:
            for move_line in moves.move_line_ids:
                if move_line.product_id:
                    # Prepare description and line data
                    description = move_line.product_id.name_get()[0][1]
                    line_data = {
                        "Item": move_line.product_id.id,
                        "description": description[:200],
                        "quantity": move_line.quantity,
                        "unitPrice": {
                            "amount": 0.0,
                            "baseAmount": 0.0,
                        },
                    }
                    doc_data["documentLines"].append(line_data)

        # Log for debugging
        _logger.info("Prepared delivery payload: %s", doc_data)
        return doc_data
    

    def get_delivery(self, id_doc):

        jasmin_connection = self._get_jasmin_connection()  # Reuse JASConnection

        url = f'{jasmin_connection.work_url}/shipping/deliveries/{id_doc}/print?template=SHIPPING_DELIVERYREPORT_PICCOLO'
        headers = {
            'Authorization': f'Bearer {jasmin_connection.access_token}',
            'Content-Type': 'application/json'
        }

        response = requests.get(url, headers=headers)
        _logger.info("Jasmin get_delivery response: %s, Status Code: %s", response.text, response.status_code)
        if response.status_code == 200:
            return response.content, self.get_delivery_doc(id_doc)
        else:
            _logger.info(f'Failed to retrieve deliverie Info: {response.status_code}, {response.text}')
            return None    
            

    def attach_document(self, document_content):

        result = self.get_delivery(document_content)
        if result is None:
            raise ValidationError(_("Failed to fetch the delivery document from Jasmim API."))


        pdf_doc, data = result
        content = base64.encodebytes(pdf_doc)

        document_name = f"{self.name}_Jasmim_Document.pdf"
        attachment = self.env['ir.attachment'].create({
            'name': document_name,
            'datas': content,
            'store_fname': document_name,
            'res_model': self._name,
            'res_id': self.id,
            'res_name': self.name,
            'type': 'binary',
            'mimetype': 'application/pdf',
        })

        return attachment, data


    def get_delivery_doc(self, id_doc):

        jasmin_connection = self._get_jasmin_connection()  # Reuse JASConnection

        url = f'{jasmin_connection.work_url}/shipping/deliveries/{id_doc}/'
        headers = {
            'Authorization': f'Bearer {jasmin_connection.access_token}',
            'Content-Type': 'application/json'
        }

        response = requests.get(url, headers=headers)
        _logger.info("Jasmin get_delivery_doc response: %s, Status Code: %s", response.text, response.status_code)
        if response.status_code == 200:
            return response.json()
        else:
            _logger.info(f'Failed to retrieve deliverie name info: {response.status_code}, {response.text}')
            return None


class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_jas_synced = fields.Boolean('Sincronizado c/ ERP')
    jas_invoice = fields.Binary('Documento PDF', attachment=False)
    doc_jasmin = fields.Char(string="Documento ERP")
    attachment_id = fields.Integer(string="attachment_id")
    filename = fields.Char('Ficheiro')

    def action_print_with_jasmim(self):
        _logger.info("Starting Jasmim sync for picking %s...", self.name)

        if self.is_jas_synced:
            _logger.info("Document for picking %s is already synced with Jasmim.", self.name)
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            pdf_url = f"{base_url}/web/content/{self.attachment_id}?download=true&inline=1"

            return {
                'type': 'ir.actions.act_url',
                'url': pdf_url,
                'target': 'new',
            }

        try:
            # Aggregate all product lines from `move_ids_without_package`
            document_content = self.send_to_jasmim(self)

            if document_content:
                # Attach the document to the picking
                attachment, data = self.attach_document(document_content)
                self.is_jas_synced = True
                self.doc_jasmin = data.get('naturalKey')
                self.jas_invoice = attachment
                self.attachment_id = attachment.id

                # Generate download URL
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                pdf_url = f"{base_url}/web/content/{attachment.id}?download=true"

                self.message_post(
                    body="Jasmin PDF added in attachment.",
                    attachment_ids=attachment.ids,
                )

                _logger.info("Successfully synced picking %s with Jasmim.", self.name)

                return {
                    'type': 'ir.actions.act_url',
                    'url': pdf_url,
                    'target': 'new',
                }

        except ValidationError as e:
            _logger.error("Failed to sync picking %s with Jasmim: %s", self.name, str(e))
            raise ValidationError(_("Failed to print Jasmim document: %s") % str(e))
