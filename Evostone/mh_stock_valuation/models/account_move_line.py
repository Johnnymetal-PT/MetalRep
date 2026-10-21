# -*- coding: utf-8 -*-

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _prepare_pdiff_svl_vals(self, corrected_layer, quantity, unit_cost, pdiff):
        """
        Override para incluir lot_group_id nos layers de diferença de preço.

        Quando uma fatura de fornecedor é validada e há diferença de preço,
        o Odoo cria stock.valuation.layer para ajustar a valorização.
        Este override garante que o lot_group_id é copiado do layer original.
        """
        vals = super()._prepare_pdiff_svl_vals(corrected_layer, quantity, unit_cost, pdiff)

        # Copiar lot_group_id do layer original (corrected_layer)
        if corrected_layer and corrected_layer.lot_group_id:
            vals['lot_group_id'] = corrected_layer.lot_group_id.id

        return vals
