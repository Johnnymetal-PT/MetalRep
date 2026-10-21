"""Sincronizacao de guias de transporte (stock.picking) com JASMIN.

Endpoint usado: ``/shipping/deliveries`` (POST + GET print).
Template de impressao: ``SHIPPING_DELIVERYREPORT_PICCOLO``.

NOTA: a JASConnection e re-instanciada em vez de reaproveitada do
contexto (custo de auth extra; aceitavel pelo volume Piccolo).

BUG conhecido: ``prepare_delivery_payload`` tem ``"company":
"PICCOLO"`` HARDCODED em vez de ``jas_connection.company``. Confirmar
antes de adicionar outra company JASMIN.
"""
import base64
import logging
from odoo import models, fields, _
from odoo.exceptions import ValidationError
from .jas_connection import JASConnection
import requests

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_jasmin_connection(self):
        """Constroi JASConnection a partir da company do move."""
        company = self.company_id

        jasmin_connection = JASConnection(
            url='https://my.jasminsoftware.com/api',
            company=company.id,
            username=company.jas_username,
            password=company.jas_password,
            tenant_key=company.jas_tenant_key,
            org_key=company.jas_org_key,
            # NOTA: codigos de documento HARDCODED aqui (nao usam os
            # campos company.jas_*) - em stock_move so chamamos
            # ``deliveries``, por isso ``fatura``/``faturaRecibo``/...
            # sao irrelevantes na pratica.
            fatura='FT',
            faturaRecibo='FR',
            faturasimplificada='FS',
        )

        if not jasmin_connection.access_token:
            raise ValidationError(_("Failed to authenticate with Jasmim API. Please check your credentials."))

        return jasmin_connection

    def send_to_jasmim(self, picking):
        """POST do picking para JASMIN deliveries."""
        jasmin_connection = self._get_jasmin_connection()
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
        """Mapeia stock.picking -> Guia de Transporte JSON JASMIN.

        BUG: ``"company": "PICCOLO"`` esta HARDCODED em vez de
        ``jas_company``. Funciona enquanto a Piccolo so tem essa
        company; revalidar se aparecer multi-company.
        """
        partner = picking.partner_id
        address = partner.contact_address

        doc_data = {
            # HARDCODED - deveria ser jas_company.
            "company": "PICCOLO",
            "Party": partner.id,
            "documentType": "GT",
            "printedReportName": "SHIPPING_DELIVERYREPORT_DEFAULT",
            "deliveryTerm": "TRANSP",
            "logisticPartyAddress": address,
            "unloadingStreetName": partner.street or "",
            "unloadingPostalZone": partner.zip or "",
            "unloadingCityName": partner.city or "",
            "documentLines": [],
        }

        # Iterar move_lines: 1 linha por move_line, descricao
        # truncada a 200 chars (limite JASMIN).
        for moves in picking.move_ids_without_package:
            for move_line in moves.move_line_ids:
                if move_line.product_id:
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

        return doc_data

    def get_delivery(self, id_doc):
        """Descarrega PDF e metadados da guia em JASMIN."""
        jasmin_connection = self._get_jasmin_connection()

        # Template PICCOLO especifico (logo, layout custom).
        url = f'{jasmin_connection.work_url}/shipping/deliveries/{id_doc}/print?template=SHIPPING_DELIVERYREPORT_PICCOLO'
        headers = {
            'Authorization': f'Bearer {jasmin_connection.access_token}',
            'Content-Type': 'application/json',
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            # Devolve tuplo (pdf_bytes, metadata_dict).
            return response.content, self.get_delivery_doc(id_doc)
        else:
            return None

    def attach_document(self, document_content):
        """Anexa o PDF da guia ao stock.move e devolve attachment + meta."""
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
        """GET metadados da guia (naturalKey, serie, numero, ...)."""
        jasmin_connection = self._get_jasmin_connection()

        url = f'{jasmin_connection.work_url}/shipping/deliveries/{id_doc}/'
        headers = {
            'Authorization': f'Bearer {jasmin_connection.access_token}',
            'Content-Type': 'application/json',
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return None


class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_jas_synced = fields.Boolean('Sincronizado c/ ERP')
    jas_invoice = fields.Binary('Documento PDF', attachment=False)
    doc_jasmin = fields.Char(string="Documento ERP")
    attachment_id = fields.Integer(string="attachment_id")
    filename = fields.Char('Ficheiro')

    def action_print_with_jasmim(self):
        """Botao do picking: sincroniza com JASMIN e abre o PDF.

        Comportamento:
        - Se ``is_jas_synced`` ja True: serve apenas o PDF existente
          (idempotente, nao cria nova guia em JASMIN).
        - Caso contrario: envia para JASMIN, anexa PDF, marca synced.

        Diferente do account_move (que cria duplicados em re-sync),
        este metodo verifica primeiro.
        """
        if self.is_jas_synced:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            pdf_url = f"{base_url}/web/content/{self.attachment_id}?download=true&inline=1"

            return {
                'type': 'ir.actions.act_url',
                'url': pdf_url,
                'target': 'new',
            }

        try:
            # Cria a guia em JASMIN.
            document_content = self.send_to_jasmim(self)

            if document_content:
                attachment, data = self.attach_document(document_content)
                self.is_jas_synced = True
                # naturalKey ex.: "GT 2026/45"
                self.doc_jasmin = data.get('naturalKey')
                self.jas_invoice = attachment
                self.attachment_id = attachment.id

                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                pdf_url = f"{base_url}/web/content/{attachment.id}?download=true"

                self.message_post(
                    body="Jasmin PDF added in attachment.",
                    attachment_ids=attachment.ids,
                )

                return {
                    'type': 'ir.actions.act_url',
                    'url': pdf_url,
                    'target': 'new',
                }

        except ValidationError as e:
            _logger.error("Failed to sync picking %s with Jasmim: %s", self.name, str(e))
            raise ValidationError(_("Failed to print Jasmim document: %s") % str(e))
