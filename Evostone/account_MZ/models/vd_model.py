from odoo import models, fields, api


class VdModel(models.Model):
    _name = 'vd.model'
    _description = 'VD Model'

    ordem_venda = fields.Many2one('sale.order', string='Ordem de venda')
    total_amount_vd = fields.Float(string='Valor total pago')
    vd_line_ids = fields.One2many('vd.line.model', 'vd_id', string='Linhas de VD')
