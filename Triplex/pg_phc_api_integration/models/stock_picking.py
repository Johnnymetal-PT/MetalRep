# -*- coding: utf-8 -*-
"""Sincronização de guias de transporte (stock.picking de saída) com o PHC (script CriaFTGT).

Ao concluir a entrega (`_action_done`), envia a guia ao PHC e anexa o PDF devolvido.
Ver o __manifest__.py.
"""

import base64
import requests

from odoo import fields, models, _
from odoo.exceptions import ValidationError, UserError

from .phc_connection import PHCConnection


class StockPicking(models.Model):
    _inherit = "stock.picking"

    x_studio_matricula = fields.Char(
        string="Matricula",
        copy=False,
        help="Vehicle plate sent to PHC in <matricula> for delivery documents.",
    )
    is_phc_synced = fields.Boolean(
        string="ERP Synced",
        default=False,
        copy=False,
        help="True if this delivery document was already synced to PHC.",
    )
    phc_document = fields.Binary(
        string="ERP PDF",
        attachment=False,
        copy=False,
        help="PDF returned by PHC.",
    )
    phc_filename = fields.Char(
        string="Ficheiro",
        copy=False,
        help="PDF name returned by PHC.",
    )
    phc_last_response = fields.Text(
        string="PHC Last Response",
        copy=False,
        help="Raw PHC SOAP response.",
    )
    phc_last_parameter = fields.Text(
        string="PHC Last Parameter",
        copy=False,
        readonly=True,
        help="CDATA payload sent to PHC inside <parameter> for the last sync attempt.",
    )

    def _phc_is_delivery_document(self):
        self.ensure_one()
        # Regra funcional da integração: apenas guias de saída concluídas para
        # cliente/transit são elegíveis para criar documento no PHC.
        return (
            self.state == "done"
            and self.picking_type_code == "outgoing"
            and self.location_dest_id.usage in ("customer", "transit")
        )

    def pre_validation(self, company):
        err_msg = ''
        base_url = (company.phc_api_base_url or '').strip()
        username = (company.phc_api_user or '').strip()
        password = (company.phc_api_password or '').strip()

        if not base_url:
            err_msg += '\n PHC WS URL'
        if not username:
            err_msg += '\n Utilizador PHC'
        if not password:
            err_msg += '\n Password PHC'
        if err_msg:
            err_msg = 'Please configure below fields in company settings: ' + err_msg
            raise ValidationError(_(err_msg))

        return base_url, username, password

    def _get_phc_connection(self):
        self.ensure_one()
        base_url, username, password = self.pre_validation(self.company_id)
        # SSL desativado por compatibilidade com instalações PHC on-prem antigas.
        return PHCConnection(
            url=base_url,
            username=username,
            password=password,
            verify_ssl=False,
        )

    def add_phc_pdf_to_attachment(self, pdf_url, pdf_name):
        self.ensure_one()
        # Faz persistência dupla: chatter/anexo + campos técnicos do documento.
        content = base64.encodebytes(requests.get(pdf_url, verify=False).content)
        attachment = self.env["ir.attachment"].create({
            "name": pdf_name,
            "datas": content,
            "store_fname": pdf_name,
            "res_model": self._name,
            "res_id": self.id,
            "res_name": self.name,
            "type": "binary",
            "mimetype": "application/pdf",
        })

        self.message_post(
            body="PHC PDF added in attachment.",
            attachment_ids=attachment.ids,
        )
        self.write({
            "phc_document": content,
            "phc_filename": pdf_name,
        })

    def connect_phc_and_sync_delivery(self):
        self.ensure_one()
        if not self._phc_is_delivery_document():
            return

        force = bool(self.env.context.get("phc_force_resync"))
        # Sem `phc_force_resync`, uma guia já sincronizada não é reenviada.
        if self.is_phc_synced and not force:
            return

        conn = self._get_phc_connection()
        payload, parameter = conn._set_template_details(
            move=self,
            phc_code="CriaFTGT",
            xml_filename="send_invoice.xml",
        )
        response, response_text = conn._sync_invoice(
            db_name=self._cr.dbname,
            move=self,
            payload=payload,
            parameter=parameter,
        )

        document_payload = None
        if isinstance(response, list) and response:
            document_payload = response[0]
        elif isinstance(response, dict):
            document_payload = response

        has_error = isinstance(document_payload, dict) and bool(document_payload.get("Erro"))
        sync_ok = bool(response) and not has_error
        # Guarda sempre request/response para auditoria e troubleshooting.
        vals = {
            "is_phc_synced": sync_ok,
            "phc_last_response": response_text,
            "phc_last_parameter": parameter,
        }
        if "CriaFTGT" not in (response_text or ""):
            vals["phc_last_response"] = "[PHC CODE=CriaFTGT]\n" + (response_text or "")
        self.write(vals)

        if sync_ok and document_payload and document_payload.get("PDF"):
            pdf_url = document_payload.get("PDF")
            pdf_name = pdf_url.rsplit("/", 1)[1]
            self.add_phc_pdf_to_attachment(pdf_url, pdf_name)
        else:
            # Extract clear error message from PHC JSON or connection failure
            error_msg = False
            if isinstance(document_payload, dict):
                error_msg = document_payload.get("Erro") or document_payload.get("Error") or document_payload.get("Mensagem")
            
            if not error_msg:
                if response_text and ("soap:Fault" in response_text or "HTTP" in response_text or "Failure" in response_text):
                    error_msg = response_text
                else:
                    error_msg = _("Falha na ligação ou resposta vazia do PHC.")
            
            raise UserError(_("Erro na integração com o PHC: %s") % error_msg)

    def action_sync_to_phc(self):
        self.ensure_one()
        self.connect_phc_and_sync_delivery()

    def action_force_sync_to_phc(self):
        self.ensure_one()
        # Entry-point manual para reprocessar guias com erro sem alterar o core flow.
        self.with_context(phc_force_resync=True).connect_phc_and_sync_delivery()

    # NOTA: a guia de transporte deixou de ser criada automaticamente ao validar a
    # entrega. A validação (`_action_done`) corre normalmente, sem chamar o PHC; a
    # criação da guia no PHC é feita manualmente no botão "Tirar Guia PHC"
    # (action_sync_to_phc). Por isso não há override de `_action_done` neste módulo.
