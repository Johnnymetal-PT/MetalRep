# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    credit_limit_minimum = fields.Float(
        string='Limite de Crédito Mínimo para Bloqueio',
        default=0.0,
        config_parameter='mh_credit_control.credit_limit_minimum',
        help='Valor mínimo do limite de crédito do cliente para ativar o bloqueio. '
             'Apenas clientes com limite de crédito >= a este valor serão bloqueados '
             'quando excederem o limite. Se 0, todos os clientes com limite definido são verificados.'
    )
