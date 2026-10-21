# -*- coding: utf-8 -*-
"""Sincronizacao de account.move com o JASMIN.

Pontos-chave do fluxo:
- Toda fatura de venda postada chama ``connect_jas_and_sync_invoice``
  via override de ``_post``. Para nao sincronizar uma fatura
  especifica, tem de se acrescentar uma flag no contexto (nao
  implementado).
- A escolha do tipo de documento JASMIN segue:
    out_refund          -> try_create_refund (Nota de Credito)
    POS, total > 100    -> jas_fr (Fatura-Recibo)
    POS, total <= 100   -> jas_fs (Fatura Simplificada)
    nao-POS             -> jas_ft (Fatura)
- O PDF certificado e anexado ao move via ``jas_invoice`` (Binary)
  e ``ir.attachment``. ``doc_jasmin`` guarda o ``naturalKey`` (ex.: FT
  2026/12).
- Re-sync MANUAL via ``action_sync_to_erp`` NAO e idempotente: corre
  o fluxo de novo e cria outro documento em JASMIN.
"""
import base64
from importlib import import_module
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    is_jas_synced = fields.Boolean('Sincronizado c/ ERP')
    jas_invoice = fields.Binary('Documento PDF', attachment=False)
    doc_jasmin = fields.Char(string="Documento ERP")
    filename = fields.Char('Ficheiro')

    def add_jas_pdf_to_attachment(self, pdf_content, pdf_name):
        """Anexa o PDF JASMIN ao move, escreve binary e devolve reload.

        Cria ``ir.attachment``, escreve ``jas_invoice`` para uso
        posterior no email (ver ``wizard/account_move_send.py``).
        """
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

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        pdf_url = f"{base_url}/web/content/{attachment.id}?download=true"

        self.message_post(
            body="Jasmin PDF added in attachment.",
            attachment_ids=attachment.ids,
        )

        # Binary direto no move serve de cache para o email do cliente
        # (wizard/account_move_send.py substitui o PDF Odoo pelo PDF JASMIN).
        self.write({
            'jas_invoice': content,
            'filename': pdf_name,
        })

        # Reload da pagina para o utilizador ver o anexo apos sync.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {'url': pdf_url},
        }

    def connect_jas_and_sync_invoice(self):
        """Replica esta fatura no JASMIN e anexa o PDF certificado."""
        conn = self._get_jas_connection()
        response = conn.authenticate()

        if response and response is True:
            self.is_jas_synced = False

            if self.journal_id.type == 'sale':
                company = self.company_id
                pos = False

                # Selecao do tipo de documento JASMIN:
                # - POS com total > 100 EUR -> Fatura-Recibo (FR)
                # - POS com total <= 100 EUR -> Fatura Simplificada (FS)
                # - Nao POS -> Fatura (FT)
                if self.pos_order_ids:
                    pos = True
                    total_amount = sum(line.price_total for line in self.invoice_line_ids)
                    if total_amount > 100:
                        TipoDoc = company.jas_fr
                    else:
                        TipoDoc = company.jas_fs
                else:
                    TipoDoc = company.jas_ft

                # Refund -> NC; restantes -> documento de venda.
                if self.move_type != 'out_refund':
                    data, as_error, pdffile, docdata = conn.try_create_sale(move=self, TipoDocInvoice=TipoDoc)
                else:
                    data, as_error, pdffile, docdata = conn.try_create_refund(move=self, TipoDocInvoice=TipoDoc, pos=pos)

                if not as_error:
                    # JASMIN devolve "ErrorMessage" mesmo em status 2xx.
                    # Tratar dict como erro funcional sem stack trace.
                    if isinstance(data, dict):
                        if data['ErrorMessage'] != "":
                            response = "dict: " + data['ErrorMessage']
                            raise ValidationError(_(str(response)))

                    document_type = docdata.get('documentType')
                    document_series = docdata.get('serie')
                    document_number = docdata.get('seriesNumber')
                    document_SAFT = docdata.get('naturalKey')

                    self.is_jas_synced = True
                    # naturalKey = chave SAFT (ex.: "FT 2026/12")
                    self.doc_jasmin = document_SAFT
                    self.message_post(body=document_SAFT)
                    self.add_jas_pdf_to_attachment(
                        pdffile, f"{document_type} {document_series}/{document_number}.pdf",
                    )

                else:
                    raise ValidationError(_("Erro: " + str(data)) + str(as_error))
        else:
            self.is_jas_synced = False

    def action_sync_to_erp(self):
        """Botao de re-sync manual.

        ATENCAO: nao e idempotente - corre o fluxo de novo e cria outro
        documento em JASMIN. Validar ``is_jas_synced`` antes de
        executar manualmente.
        """
        self.ensure_one()
        self.connect_jas_and_sync_invoice()

    def _post(self, soft=True):
        """Override do posting para disparar sync automatico.

        Qualquer fatura de venda postada e replicada para JASMIN.
        Para excluir uma fatura especifica seria preciso introduzir
        uma flag de contexto (NAO implementado).
        """
        moves = super(AccountMove, self)._post(soft)

        for move in moves:
            if move.journal_id.type == 'sale':
                # NOTA: o `moves.id` original era ambiguo em batch;
                # mantido para preservar comportamento mas validar em
                # imports massivos.
                move = self.env['account.move'].browse(moves.id)
                move.connect_jas_and_sync_invoice()

        return moves

    @staticmethod
    def pre_validation(company):
        """Valida que a company tem todas as credenciais JASMIN."""
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
        """Cria conexao JASMIN para a company desta fatura.

        Usa ``import_module`` em vez de import normal para evitar
        import circular durante o registry boot.
        """
        self.ensure_one()

        company = self.company_id
        self.pre_validation(company)
        connector = import_module(
            'odoo.addons.pg_jasmin_integration.models.jas_connection')
        return (getattr(connector, 'JASConnection')(
            url='https://my.jasminsoftware.com/api',
            company=company.jas_company,
            username=company.jas_username,
            password=company.jas_password,
            tenant_key=company.jas_tenant_key,
            org_key=company.jas_org_key,
            fatura=company.jas_ft,
            faturaRecibo=company.jas_fr,
            faturasimplificada=company.jas_fs,
        ))
