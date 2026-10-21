# Copyright 2025 MH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools.float_utils import float_compare


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # Link para nota de crédito criada a partir desta devolução
    credit_note_id = fields.Many2one(
        'account.move',
        string='Nota de Crédito',
        copy=False,
        readonly=True,
        help='Nota de crédito gerada a partir desta devolução'
    )

    credit_note_count = fields.Integer(
        string='Nº Notas de Crédito',
        compute='_compute_credit_note_count'
    )

    fully_returned = fields.Boolean(
        string='Totalmente Devolvido',
        compute='_compute_fully_returned',
        help='Verdadeiro quando esta SAÍDA já não tem quantidade por devolver '
             '(entregue − devoluções já existentes ≤ 0). Usado para esconder o '
             'botão Devolução e impedir devoluções duplicadas.',
    )

    is_sale_return = fields.Boolean(
        string='É Devolução de Venda',
        compute='_compute_is_sale_return',
        help='Verdadeiro quando este picking é ele próprio uma devolução '
             '(tem return_id) originada numa venda (tem sale_id). Usado para '
             'esconder o botão Devolução — não se devolve uma devolução de venda.',
    )

    @api.depends('return_id', 'sale_id')
    def _compute_is_sale_return(self):
        for picking in self:
            picking.is_sale_return = bool(picking.return_id) and bool(picking.sale_id)

    @api.depends('credit_note_id')
    def _compute_credit_note_count(self):
        for picking in self:
            picking.credit_note_count = 1 if picking.credit_note_id else 0

    @api.depends(
        'state', 'picking_type_code',
        'move_ids.quantity', 'move_ids.product_uom',
        'move_ids.move_dest_ids.product_uom_qty',
        'move_ids.move_dest_ids.state',
        'move_ids.move_dest_ids.origin_returned_move_id',
    )
    def _compute_fully_returned(self):
        """Uma SAÍDA está totalmente devolvida quando, para todos os
        movimentos entregues, a quantidade devolvida (em qualquer devolução
        NÃO cancelada — draft/waiting/confirmed/assigned/done, ou seja, mesmo
        antes de validar) iguala ou excede a quantidade entregue.

        Só se aplica a pickings de SAÍDA (outgoing) concluídos.
        """
        for picking in self:
            fully = False
            if picking.picking_type_code == 'outgoing' and picking.state == 'done':
                delivered_moves = picking.move_ids.filtered(
                    lambda m: m.product_id and m.quantity > 0)
                if delivered_moves:
                    fully = True
                    for move in delivered_moves:
                        returned = sum(
                            dest.product_uom_qty
                            for dest in move.move_dest_ids
                            if dest.origin_returned_move_id.id == move.id
                            and dest.state != 'cancel'
                        )
                        rounding = move.product_uom.rounding
                        if float_compare(move.quantity - returned, 0.0,
                                         precision_rounding=rounding) > 0:
                            fully = False
                            break
            picking.fully_returned = fully

    def action_view_credit_note(self):
        """Abrir a nota de crédito associada"""
        self.ensure_one()
        if not self.credit_note_id:
            return

        return {
            'name': 'Nota de Crédito',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.credit_note_id.id,
            'context': {'create': False}
        }
