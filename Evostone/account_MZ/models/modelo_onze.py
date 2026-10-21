from odoo import models, fields, api


class ModeloOnze(models.Model):
    _name = 'modelo.onze'
    _description = 'Modelo 11'

    dependente = fields.One2many('dependentes.copy', 'modelo_onze', string='Dependente')
    employee_id = fields.Many2one('hr.employee', string='Funcionário')
