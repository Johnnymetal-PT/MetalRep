# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    stock_adjustment_deficit_account_id = fields.Many2one(
        'account.account',
        related='company_id.stock_adjustment_deficit_account_id',
        readonly=False,
        string='Conta Deficit Acerto de Stock',
        help='Conta a debitar para défices de stock (ex: 6843 Défice de Existências).',
    )

    stock_adjustment_surplus_account_id = fields.Many2one(
        'account.account',
        related='company_id.stock_adjustment_surplus_account_id',
        readonly=False,
        string='Conta Excedente Acerto de Stock',
        help='Conta a creditar para excedentes de stock (ex: 789003 Proveito Existências).',
    )
