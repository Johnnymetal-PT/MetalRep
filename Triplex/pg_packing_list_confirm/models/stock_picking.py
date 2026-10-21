# -*- coding: utf-8 -*-
"""Bloqueia a validação da expedição enquanto o packing list não for confirmado.

Ver o __manifest__.py para o objetivo. Aplica-se só a transferências de saída.
"""
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    packing_list_confirmada = fields.Boolean(
        string='Packing List Confirmada',
        default=False,
        help='Indicates if the packing list has been confirmed for this delivery.'
    )

    def button_validate(self):
        # Entre as transferências a validar, isola as de SAÍDA ainda não confirmadas.
        outgoing_without_confirmation = self.filtered(
            lambda picking: picking.picking_type_code == 'outgoing' and not picking.packing_list_confirmada
        )

        # Se existir alguma, impede a validação até o packing list ser confirmado.
        if outgoing_without_confirmation:
            raise UserError(_("You must confirm the packing list before validating the delivery."))

        return super().button_validate()
