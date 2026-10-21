from odoo import models, fields, api


class CaeModel(models.Model):
    _name = 'cae.model'
    _description = 'Cae Model'

    ascendente_id = fields.Many2one('cae.model', string='Ascendente')
    cae_main = fields.Boolean(string='Principal')
    descendente = fields.One2many('cae.model', 'ascendente_id', string='Descendente')
    name = fields.Char(string='Codigo')
    nome = fields.Char(string='Nome')
