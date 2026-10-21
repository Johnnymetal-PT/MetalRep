# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    mh_purchase_return = fields.Boolean(
        string='Devolução de Mercadoria',
        compute='_compute_mh_purchase_return', store=True,
        help="Verdadeiro quando a NC de compra é uma devolução de mercadoria "
             "(ligada a um picking de devolução). Nesse caso a linha lança na "
             "conta de devoluções da categoria (ex.: 217), em vez da conta de "
             "gasto/compras. Automático — não editável.")

    @api.depends('move_type', 'return_picking_id')
    def _compute_mh_purchase_return(self):
        """Automático (readonly): NC de compra ligada a um picking de devolução."""
        for move in self:
            move.mh_purchase_return = bool(
                move.move_type == 'in_refund' and move.return_picking_id)
