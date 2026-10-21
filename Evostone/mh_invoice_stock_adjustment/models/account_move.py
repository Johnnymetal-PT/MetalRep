# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    stock_adjustment_move_id = fields.Many2one(
        'account.move',
        string='Lançamento de Acerto de Stock',
        readonly=True,
        copy=False,
        help='Lançamento STJ gerado para acertar diferenças entre recepção e facturação.',
    )

    stock_adjustment_state = fields.Selection(
        selection=[
            ('none', 'Sem ajuste'),
            ('surplus', 'Excedente'),
            ('deficit', 'Défice'),
            ('mixed', 'Misto'),
        ],
        string='Estado Acerto Stock',
        compute='_compute_stock_adjustment_state',
        store=True,
    )

    @api.depends('stock_adjustment_move_id')
    def _compute_stock_adjustment_state(self):
        for move in self:
            if not move.stock_adjustment_move_id:
                move.stock_adjustment_state = 'none'
                continue
            ref = move.stock_adjustment_move_id.ref or ''
            if 'Misto' in ref:
                move.stock_adjustment_state = 'mixed'
            elif 'Excedente' in ref:
                move.stock_adjustment_state = 'surplus'
            elif 'Défice' in ref or 'Deficit' in ref:
                move.stock_adjustment_state = 'deficit'
            else:
                move.stock_adjustment_state = 'none'

    # ------------------------------------------------------------------
    # Override button_draft - cancelar STJ de acerto ao voltar a rascunho
    # ------------------------------------------------------------------

    def button_draft(self):
        # Cancelar STJ de acerto antes de voltar a rascunho
        for move in self:
            if move.stock_adjustment_move_id and move.stock_adjustment_move_id.state == 'posted':
                move.stock_adjustment_move_id.button_draft()
                move.stock_adjustment_move_id.button_cancel()
                _logger.info("Factura %s: STJ de acerto %s cancelado", move.name or move.id, move.stock_adjustment_move_id.name)
            move.stock_adjustment_move_id = False
        return super().button_draft()

    # ------------------------------------------------------------------
    # Override _post
    # ------------------------------------------------------------------

    def _post(self, soft=True):
        # Chamar super() para postar a factura
        posted = super()._post(soft=soft)

        # DEPOIS de super(): Criar STJ para todas as linhas com diferença
        for move in posted:
            if move.move_type != 'in_invoice':
                continue
            adjustments = move._compute_stock_qty_adjustments()
            if not adjustments or not adjustments['lines']:
                continue
            move._create_stock_adjustment_entry(adjustments)

        return posted

    # ------------------------------------------------------------------
    # Calcular diferenças qty recebida vs facturada
    # ------------------------------------------------------------------

    def _compute_stock_qty_adjustments(self):
        """
        Para cada linha da factura com purchase_line_id:
        1. Obter stock moves done
        2. Calcular diff = qty_received - qty_invoiced
        3. Calcular diff_value em MOEDA DA EMPRESA (MZN) usando custo do stock move
        4. Calcular diff_value em MOEDA DA FACTURA para linha de deficit

        Cada linha é tratada individualmente (pode ser surplus ou deficit).
        """
        self.ensure_one()
        lines = []
        company_currency = self.company_id.currency_id
        invoice_currency = self.currency_id
        is_foreign = company_currency != invoice_currency

        for inv_line in self.invoice_line_ids.filtered(
            lambda l: l.display_type == 'product' and l.purchase_line_id
        ):
            po_line = inv_line.purchase_line_id
            stock_moves = po_line.move_ids.filtered(lambda m: m.state == 'done')
            if not stock_moves:
                continue

            qty_received = sum(stock_moves.mapped('quantity'))
            qty_invoiced = inv_line.quantity

            diff_qty = qty_received - qty_invoiced
            if diff_qty == 0:
                continue

            # Valor em moeda da factura (considerando desconto)
            price_after_discount = inv_line.price_unit * (1 - (inv_line.discount or 0.0) / 100.0)
            diff_value_currency = diff_qty * price_after_discount

            # Valor em moeda da empresa (MZN) para o STJ
            if is_foreign:
                if diff_qty > 0:
                    # Surplus: usar unit_cost do SVL (taxa da data de validação)
                    # porque as unidades excedentes estão em stock ao custo real de recepção
                    svls = stock_moves.sudo().stock_valuation_layer_ids.filtered(
                        lambda s: s.quantity > 0
                    )
                    if svls:
                        total_svl_value = sum(svls.mapped('value'))
                        total_svl_qty = sum(svls.mapped('quantity'))
                        unit_cost_company = total_svl_value / total_svl_qty if total_svl_qty else 0
                    else:
                        unit_cost_company = abs(stock_moves[0].price_unit)
                    diff_value_company = diff_qty * unit_cost_company
                else:
                    # Deficit: usar taxa da invoice_date para alinhar com a fatura
                    # (a fatura converte usando invoice_date, não date contabilística)
                    convert_date = self.invoice_date or self.date or fields.Date.context_today(self)
                    diff_value_company = invoice_currency._convert(
                        diff_value_currency,
                        company_currency,
                        self.company_id,
                        convert_date,
                    )
            else:
                diff_value_company = diff_value_currency

            account_211 = inv_line.product_id.categ_id.property_stock_account_input_categ_id
            if not account_211:
                _logger.warning(
                    "Produto %s (categ %s) sem conta de input de stock configurada. "
                    "A ignorar para acerto.",
                    inv_line.product_id.name,
                    inv_line.product_id.categ_id.name,
                )
                continue

            lines.append({
                'product': inv_line.product_id,
                'account_211': account_211,
                'diff_qty': diff_qty,
                'diff_value_company': diff_value_company,
                'diff_value_currency': diff_value_currency,
                'price_unit': inv_line.price_unit,
            })

        if not lines:
            return {}

        return {
            'is_foreign': is_foreign,
            'lines': lines,
        }

    # ------------------------------------------------------------------
    # Criar lançamento STJ de acerto (por linha, surplus e deficit)
    # ------------------------------------------------------------------

    def _create_stock_adjustment_entry(self, adjustments):
        """
        Cria lançamento STJ em MOEDA DA EMPRESA (MZN).
        Cada linha é tratada individualmente:

        Linha com diff > 0 (surplus):
            Débito 211xx: valor MZN  /  Crédito 789003 (Proveito Existências)
        Linha com diff < 0 (deficit):
            Crédito 211xx: |valor| MZN  /  Débito conta deficit (configurável)
        """
        self.ensure_one()

        journal = self.env['account.journal'].search(
            [('code', '=', 'STJ')], limit=1
        )
        if not journal:
            raise UserError(_(
                "Diário STJ (Valorização de Inventário) não encontrado. "
                "Verifique a configuração."
            ))

        surplus_account = self._get_surplus_account()
        has_deficit_lines = any(l['diff_value_company'] < 0 for l in adjustments['lines'])
        has_surplus_lines = any(l['diff_value_company'] > 0 for l in adjustments['lines'])

        if has_surplus_lines and not surplus_account:
            raise UserError(_(
                "Conta 789003 (Proveito Existências) não encontrada. "
                "Verifique a configuração contabilística."
            ))

        deficit_account = None
        if has_deficit_lines:
            deficit_account = self._get_deficit_account()

        company_currency = self.company_id.currency_id
        line_ids = []
        total_surplus_credit = 0.0   # contrapartida surplus → crédito 789003
        total_deficit_debit = 0.0    # contrapartida deficit → débito conta deficit

        # Linhas por produto/conta 211xx — cada uma com o seu sentido
        for adj_line in adjustments['lines']:
            value = adj_line['diff_value_company']
            abs_value = company_currency.round(abs(value))
            is_line_surplus = value > 0

            line_ids.append((0, 0, {
                'account_id': adj_line['account_211'].id,
                'debit': abs_value if is_line_surplus else 0.0,
                'credit': abs_value if not is_line_surplus else 0.0,
                'name': "Acerto stock %s (%.2f un %s)" % (
                    adj_line['product'].name,
                    abs(adj_line['diff_qty']),
                    'excedente' if is_line_surplus else 'défice',
                ),
            }))

            if is_line_surplus:
                total_surplus_credit += abs_value
            else:
                total_deficit_debit += abs_value

        # Contrapartida surplus → Crédito 789003
        if total_surplus_credit > 0:
            line_ids.append((0, 0, {
                'account_id': surplus_account.id,
                'debit': 0.0,
                'credit': company_currency.round(total_surplus_credit),
                'name': "Proveito existências (excedente) - %s" % (self.name or ''),
            }))

        # Contrapartida deficit → Débito conta deficit (configurável)
        if total_deficit_debit > 0:
            line_ids.append((0, 0, {
                'account_id': deficit_account.id,
                'debit': company_currency.round(total_deficit_debit),
                'credit': 0.0,
                'name': "Défice de existências - %s" % (self.name or ''),
            }))

        # Determinar tipo para o ref
        has_surplus = total_surplus_credit > 0
        has_deficit = total_deficit_debit > 0
        if has_surplus and has_deficit:
            adj_type = 'Misto'
        elif has_surplus:
            adj_type = 'Excedente'
        else:
            adj_type = 'Défice'

        stj_move = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': journal.id,
            'date': self.date or fields.Date.context_today(self),
            'ref': "Acerto stock %s - %s" % (adj_type, self.name or ''),
            'line_ids': line_ids,
        })
        stj_move.action_post()

        self.stock_adjustment_move_id = stj_move.id

        _logger.info(
            "Factura %s: Criado lançamento STJ %s (%s) surplus=%.2f (789003) deficit=%.2f (%s) MZN%s",
            self.name or self.id,
            stj_move.name,
            adj_type,
            total_surplus_credit,
            total_deficit_debit,
            deficit_account.code if deficit_account else 'N/A',
            " (factura em %s)" % self.currency_id.name if adjustments['is_foreign'] else '',
        )

    # ------------------------------------------------------------------
    # Helper: obter conta surplus (789003)
    # ------------------------------------------------------------------

    def _get_surplus_account(self):
        """Conta a creditar para excedentes de stock:
        1. Conta definida nos Settings da empresa
        2. Senão, fallback: procura a conta 789003 (Proveito Existências) por code_store.
        """
        account = self.company_id.stock_adjustment_surplus_account_id
        if account:
            return account
        return self.env['account.account'].search(
            [('code_store', 'like', '789003')], limit=1
        )

    # ------------------------------------------------------------------
    # Helper: obter conta deficit (configurável)
    # ------------------------------------------------------------------

    def _get_deficit_account(self):
        """
        Determina a conta a debitar para défice de stock:
        1. Se existe linha manual com acerto_de_stock=True → usar a conta dessa linha
        2. Senão → usar a conta definida nos Settings da empresa
        3. Se nenhuma → raise UserError
        """
        self.ensure_one()
        # 1) Verificar se existe artigo manual com acerto_de_stock
        manual_line = self.invoice_line_ids.filtered(
            lambda l: l.product_id and l.product_id.acerto_de_stock
        )
        if manual_line:
            return manual_line[0].account_id

        # 2) Usar conta dos Settings da empresa
        account = self.company_id.stock_adjustment_deficit_account_id
        if account:
            return account

        # 3) Nenhuma configurada
        raise UserError(_(
            "Conta de deficit para acerto de stock não configurada.\n"
            "Defina a conta em: Definições → Contabilidade → Acerto de Stock → Conta Deficit\n"
            "Ou adicione manualmente um artigo com 'Acerto de Stock' marcado na factura."
        ))
