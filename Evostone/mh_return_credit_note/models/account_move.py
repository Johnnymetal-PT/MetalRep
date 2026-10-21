# Copyright 2025 MH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.float_utils import float_compare


class AccountMove(models.Model):
    _inherit = 'account.move'

    # Link para picking de devolução que originou esta nota de crédito
    return_picking_id = fields.Many2one(
        'stock.picking',
        string='Picking de Devolução',
        copy=False,
        readonly=True,
        help='Picking de devolução que originou esta nota de crédito'
    )

    # Picking de origem (entrega original)
    origin_picking_id = fields.Many2one(
        'stock.picking',
        string='Picking Original',
        copy=False,
        readonly=True,
        help='Picking de entrega original'
    )

    credit_note_reason = fields.Char(
        string='Motivo',
        copy=False,
        help='Motivo da nota de crédito'
    )

    is_fully_credited = fields.Boolean(
        string='Totalmente Creditada',
        compute='_compute_is_fully_credited',
        help='Verdadeiro quando as notas de crédito não canceladas já fecham o '
             'valor total da factura. Usado para impedir notas de crédito '
             'duplicadas de valor total.',
    )

    @api.constrains('invoice_date', 'move_type')
    def _check_credit_note_date(self):
        for move in self:
            if move.move_type != 'out_refund' or not move.invoice_date:
                continue

            last_credit_note = self.search([
                ('move_type', '=', 'out_refund'),
                ('state', '=', 'posted'),
                ('company_id', '=', move.company_id.id),
                ('invoice_date', '!=', False),
                ('id', '!=', move.id),
            ], order='invoice_date desc', limit=1)

            if last_credit_note and move.invoice_date < last_credit_note.invoice_date:
                raise ValidationError(_(
                    'A data da Nota de Crédito (%(date)s) não pode ser inferior à última '
                    'Nota de Crédito emitida (%(last_ref)s de %(last_date)s).',
                    date=move.invoice_date.strftime('%d/%m/%Y'),
                    last_ref=last_credit_note.name or 'Rascunho',
                    last_date=last_credit_note.invoice_date.strftime('%d/%m/%Y'),
                ))

    @api.depends(
        'move_type', 'amount_total', 'currency_id',
        'reversal_move_ids', 'reversal_move_ids.state',
        'reversal_move_ids.amount_total',
    )
    def _compute_is_fully_credited(self):
        """True quando as notas de crédito NÃO canceladas que revertem esta
        factura já somam (ou excedem) o total da factura — ou seja, a factura
        está totalmente creditada. Usado para esconder/bloquear a criação de
        nova nota de crédito de valor total (duplicada)."""
        for move in self:
            fully = False
            if move.move_type in ('out_invoice', 'in_invoice') and move.amount_total:
                credited = sum(
                    cn.amount_total for cn in move.reversal_move_ids
                    if cn.state != 'cancel'
                )
                rounding = move.currency_id.rounding or 0.01
                if float_compare(credited, move.amount_total,
                                 precision_rounding=rounding) >= 0:
                    fully = True
            move.is_fully_credited = fully

    def action_reverse(self):
        """Reforço (defesa em profundidade): impedir gerar nova nota de crédito
        quando a factura JÁ está totalmente creditada — evita a NC duplicada de
        valor total. Mesmo que o botão apareça, o método recusa."""
        for move in self:
            if move.is_fully_credited:
                ncs = move.reversal_move_ids.filtered(lambda m: m.state != 'cancel')
                raise UserError(_(
                    'A factura "%(inv)s" já está totalmente creditada pela(s) '
                    'nota(s) de crédito: %(ncs)s.\n\nNão é possível gerar outra '
                    'nota de crédito de valor total.'
                ) % {
                    'inv': move.name or '',
                    'ncs': ', '.join(ncs.mapped('name')) or _('(rascunho)'),
                })
        return super().action_reverse()
