# -*- coding: utf-8 -*-
import logging
from collections import defaultdict

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    cogs_price_diff_move_id = fields.Many2one(
        'account.move',
        string='Ajuste CMV Diferença de Preço',
        copy=False,
        readonly=True,
        help='Lançamento criado por este módulo para encaminhar a diferença de '
             'preço da parte vendida (cogs auto-canceladas) para o CMV.',
    )

    # ------------------------------------------------------------------
    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        for move in posted.filtered(
            lambda m: m.move_type == 'in_invoice' and not m.cogs_price_diff_move_id
        ):
            move._mh_route_cogs_price_diff_to_output()
        return posted

    # ------------------------------------------------------------------
    def _mh_get_cogs_correction_journal(self):
        """Diário para o lançamento de correcção:
        1. Conta definida nos Settings da empresa (cogs_price_diff_journal_id)
        2. Senão, parâmetro de sistema mh_purchase_cogs_price_diff.journal_id
        3. Senão, primeiro diário 'general' da empresa."""
        self.ensure_one()
        journal = self.company_id.cogs_price_diff_journal_id
        if journal:
            return journal
        param = self.env['ir.config_parameter'].sudo().get_param(
            'mh_purchase_cogs_price_diff.journal_id'
        )
        if param:
            journal = self.env['account.journal'].browse(int(param)).exists()
            if journal:
                return journal
        return self.env['account.journal'].search([
            ('type', '=', 'general'),
            ('company_id', '=', self.company_id.id),
        ], limit=1)

    def _mh_route_cogs_price_diff_to_output(self):
        """Detecta as linhas `cogs` que se anulam na conta de stock input
        (porque a conta de despesa == conta de input) e lança a correcção
        D CMV / C input (parte vendida → CMV).

        NÃO mexe na conta de valorização (261) nem no value_svl — só transfere
        o custo extra da venda da conta de trânsito para o CMV.

        Só actua quando a PO associada à factura NÃO tem Documento de Importação
        (IMP). Se tiver, é o fluxo de importação (Ajuste de Importação / ADJ) que
        trata o custo da parte vendida — este módulo não interfere.
        """
        self.ensure_one()

        # NOTA: também actua em facturas de importação. As linhas `cogs` vêm das
        # linhas de PRODUTO com PO (diferença de preço bill vs recepção da parte
        # vendida) e são disjuntas das linhas ÓRFÃS (sem PO) que o fluxo de
        # Ajuste de Importação (ADJ) trata. Não há sobreposição, logo não há
        # duplicação de custo.

        cogs_lines = self.line_ids.filtered(
            lambda l: l.display_type == 'cogs' and l.product_id
        )
        if not cogs_lines:
            return

        # agrupar por produto
        by_product = defaultdict(lambda: self.env['account.move.line'])
        for line in cogs_lines:
            by_product[line.product_id] |= line

        cur = self.company_id.currency_id
        corr_lines = []
        for product, lines in by_product.items():
            # Conta de trânsito = a conta REAL onde as cogs caíram (fonte de
            # verdade do que o Odoo lançou), não a configurada na categoria.
            transit = lines.mapped('account_id')
            if len(transit) != 1:
                # cogs espalhadas por várias contas → não é o auto-cancelamento
                continue

            # só actua se as cogs se ANULAM nessa conta (D == C)
            debit_amt = sum(lines.mapped('debit'))
            credit_amt = sum(lines.mapped('credit'))
            if cur.round(debit_amt - credit_amt) != 0:
                continue
            amount = cur.round(debit_amt)
            if not amount:
                continue

            # CMV (saída de stock) da categoria do produto; se for a própria
            # conta de trânsito, não há nada a encaminhar.
            output = product.product_tmpl_id.get_product_accounts().get('stock_output')
            if not output or output.id == transit.id:
                continue

            # Direcção: comparar o valor de ENTRADA (recepção) com o valor
            # FATURADO, por unidade e em moeda da empresa (o balance já reflecte
            # o câmbio da factura; o SVL de recepção reflecte o câmbio da entrada).
            #   faturado >= recepção → preço subiu → D CMV / C trânsito
            #   faturado <  recepção → preço desceu → D trânsito / C CMV
            prod_lines = self.invoice_line_ids.filtered(
                lambda l: l.product_id == product and l.display_type == 'product'
            )
            bill_qty = sum(prod_lines.mapped('quantity'))
            bill_unit = (sum(prod_lines.mapped('balance')) / bill_qty) if bill_qty else 0.0

            recv = prod_lines.mapped(
                'purchase_line_id.move_ids.stock_valuation_layer_ids'
            ).filtered(lambda s: s.quantity > 0)
            recv_qty = sum(recv.mapped('quantity'))
            recv_unit = (sum(recv.mapped('value')) / recv_qty) if recv_qty else bill_unit

            if bill_unit >= recv_unit:
                debit_acc, credit_acc = output, transit   # preço subiu
            else:
                debit_acc, credit_acc = transit, output   # preço desceu

            label = _('Ajuste CMV diferença preço vendido — %(prod)s (%(name)s)') % {
                'prod': product.display_name,
                'name': self.name,
            }
            corr_lines.append((0, 0, {
                'account_id': debit_acc.id, 'debit': amount, 'credit': 0.0,
                'product_id': product.id, 'name': label,
            }))
            corr_lines.append((0, 0, {
                'account_id': credit_acc.id, 'debit': 0.0, 'credit': amount,
                'product_id': product.id, 'name': label,
            }))

        if not corr_lines:
            return

        journal = self._mh_get_cogs_correction_journal()
        if not journal:
            _logger.warning(
                'mh_purchase_cogs_price_diff: sem diário general para %s', self.name)
            return

        correction = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': journal.id,
            'date': self.date,
            'ref': _('Ajuste CMV diferença preço vendido — %s') % self.name,
            'line_ids': corr_lines,
        })
        correction.action_post()
        self.cogs_price_diff_move_id = correction.id
        _logger.info(
            'mh_purchase_cogs_price_diff: factura %s → correcção CMV %s',
            self.name, correction.name)
