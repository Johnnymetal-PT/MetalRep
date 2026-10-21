# -*- coding: utf-8 -*-
"""Sincronização de faturas (account.move) com o PHC e anexação do PDF oficial.

Ao publicar (`_post`), envia a fatura ao PHC (via PHCConnection) e guarda a resposta/PDF.
Ver o __manifest__.py para o guia completo.
"""

import base64
import requests
from odoo import models, fields, _
from importlib import import_module
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round


class AccountMove(models.Model):
    _inherit = "account.move"

    is_phc_synced = fields.Boolean('ERP Synced')
    phc_invoice = fields.Binary('ERP PDF', attachment=False)
    filename = fields.Char('Ficheiro')
    phc_last_response = fields.Text('PHC Last Response')

    def add_phc_pdf_to_attachment(self, pdf_url, pdf_name):
        self.ensure_one()
        # O endpoint PHC devolve URL direta para o PDF; este download usa verify=False
        # para manter compatibilidade com ambientes com certificados internos.
        content = base64.encodebytes(requests.get(pdf_url, verify=False).content)
        attachment = self.env['ir.attachment'].create({
            'name': pdf_name,
            'datas': content,
            'store_fname': pdf_name,
            'res_model': self._name,
            'res_id': self.id,
            'res_name': self.name,
            'type': 'binary',
            'mimetype': 'application/pdf'
        })

        self.message_post(
            body="PHC PDF added in attachment.",
            attachment_ids=attachment.ids
        )

        self.write({
            'phc_invoice': content,
            'filename': pdf_name
        })

    def connect_phc_and_sync_invoice(self):
        self.ensure_one()
        # Proteção: este fluxo é apenas para documentos de venda (inclui recibos).
        if not self.is_sale_document(include_receipts=True):
            return

        conn = self._get_phc_connection()
        payload, parameter = conn._set_template_details(move=self)
        response, response_text = conn._sync_invoice(
            db_name=self._cr.dbname, move=self, payload=payload, parameter=parameter)

        invoice_payload = None
        if isinstance(response, list) and response:
            invoice_payload = response[0]
        elif isinstance(response, dict):
            invoice_payload = response

        # O conector marca "synced" apenas quando PHC devolve PDF válido.
        # Sem PDF, assume-se falha funcional da integração.
        if invoice_payload and invoice_payload.get('PDF'):
            self.is_phc_synced = True
            pdf_url = invoice_payload.get('PDF')
            pdf_name = pdf_url.rsplit('/', 1)[1]
            self.add_phc_pdf_to_attachment(pdf_url, pdf_name)
        else:
            self.is_phc_synced = False

        self.phc_last_response = response_text

    def action_sync_to_phc(self):
        self.ensure_one()
        self.connect_phc_and_sync_invoice()

    def _post(self, soft=True):
        # Gatilho automático: ao publicar uma fatura/recibo de venda, sincroniza com o PHC.
        moves = super(AccountMove, self)._post(soft)
        # A filtragem evita chamadas PHC desnecessárias em documentos sem âmbito.
        for move in moves.filtered(lambda m: m.is_sale_document(include_receipts=True)):
            move.connect_phc_and_sync_invoice()
        return moves

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
        # Import dinâmico para usar a implementação ativa do módulo sem acoplamento
        # de import no topo (útil em cenários de migração/legacy).
        connector = import_module(
            'odoo.addons.pg_phc_api_integration.models.phc_connection')
        return getattr(connector, 'PHCConnection')(
            url=base_url,
            username=username,
            password=password,
            verify_ssl=False,
        )


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def get_analytic_distribution_tags(self):
        self.ensure_one()
        analytic_tags = []
        if self.analytic_distribution:
            AnalyticAccount = self.env['account.analytic.account']
            distribution = []
            account_totals = {}
            # analytic_distribution vem como {"id,id": percentagem, ...}; aqui
            # converte-se para estrutura navegável por conta e por plano.
            for account_ids in self.analytic_distribution:
                defaultVals = []
                ids = account_ids.split(',')

                for account_id in ids:
                    account = AnalyticAccount.browse(int(account_id))
                    defaultVals.append({
                        'account_id': int(account_id),
                        'account_display_name': account.display_name,
                        'account_root_plan_id': account.root_plan_id.id,
                    })
                distribution.append({
                    'analytic_accounts': defaultVals,
                    'percentage': self.analytic_distribution[account_ids] / 100,
                })

            analytic_account_dict = {}
            for line in distribution:
                for column in line['analytic_accounts']:
                    total = float_round(line['percentage'], precision_digits=2)
                    if not analytic_account_dict.get(column['account_id']):
                        analytic_account_dict.update({
                            column['account_id']: {
                                'total': total
                            }
                        })
                    else:
                        analytic_account_dict[column['account_id']]['total'] = \
                            analytic_account_dict.get(
                            column.get('account_id')).get('total') + total

                    if not account_totals.get(column.get('account_root_plan_id')):
                        account_totals[column['account_root_plan_id']] = {}

                    account_totals[column['account_root_plan_id']][column['account_id']] = {
                        'acc_name': column['account_display_name'],
                        'total': analytic_account_dict.get(
                            column.get('account_id')).get('total'),
                    }

            for acc_vals in account_totals:
                index = 0
                text = ''
                # Produz texto final no formato "xx% Conta A | yy% Conta B",
                # agrupado por root_plan_id.
                for acc in account_totals[acc_vals]:
                    name = ''
                    if float_round(account_totals[acc_vals][acc]['total'], precision_digits=2) == 1:
                        name = account_totals[acc_vals][acc]['acc_name']
                    else:
                        name = str(float_round(
                            account_totals[acc_vals][acc]['total'] * 100,
                            precision_digits=2)) + "% " + \
                            account_totals[acc_vals][acc]['acc_name']

                    if index != 0:
                        text += ' | ' + name
                    else:
                        text += name
                    index += 1
                analytic_tags.append(text)

        return analytic_tags
