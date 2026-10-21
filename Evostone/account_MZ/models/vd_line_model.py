from odoo import models, fields, api


class VdLineModel(models.Model):
    _name = 'vd.line.model'
    _description = 'VD Line Model'

    invoice_id = fields.Many2one('account.move', string='Fatura')
    metodo_pagamento = fields.Many2one('account.payment.method.line', string='Método de pagamento')
    valor = fields.Float(string='Valor')
    vd_id = fields.Many2one('vd.model', string='VD')
