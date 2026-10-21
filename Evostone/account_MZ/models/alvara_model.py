from odoo import models, fields


class AlvaraModel(models.Model):
    _name = 'alvara.model'
    _description = 'Alvara'

    act_main = fields.Char(string='Act Main')
    cae_ids = fields.Many2many('cae.model', 'cae_model_alvara_model_rel', 'alvara_id', 'cae_id', string='Cae Ids')
    data_emissao = fields.Date(string='Data Emissao')
    ficheiro = fields.Binary(string='Ficheiro')
    name = fields.Char(string='Name')
    numero = fields.Char(string='Numero')
    validade = fields.Date(string='Validade')
