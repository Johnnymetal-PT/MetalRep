# -*- coding: utf-8 -*-

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    stock_adjustment_deficit_account_id = fields.Many2one(
        'account.account',
        string='Conta Deficit Acerto de Stock',
        help='Conta a debitar para défices de stock (ex: 6843 Défice de Existências). '
             'Usada quando não existe artigo manual com acerto_de_stock na factura.',
    )

    stock_adjustment_surplus_account_id = fields.Many2one(
        'account.account',
        string='Conta Excedente Acerto de Stock',
        help='Conta a creditar para excedentes de stock (ex: 789003 Proveito Existências). '
             'Usada quando recebeu mais do que facturou.',
    )
