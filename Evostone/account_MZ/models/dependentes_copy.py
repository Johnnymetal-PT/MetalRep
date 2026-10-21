from odoo import models, fields, api


class DependentesCopy(models.Model):
    _name = 'dependentes.copy'
    _description = 'dependentes copy'

    colaborador = fields.Many2one('hr.employee', string='Colaborador')
    data_de_nascimento = fields.Date(string='Data de Nascimento')
    dependente = fields.Char(string='Dependente')
    documento = fields.Binary(string='Documento')
    grau_parentesco = fields.Selection([], string='Grau Parentesco')
    modelo_onze = fields.Many2one('modelo.onze', string='modelo onze')
    numero_do_documento = fields.Char(string='Número do Documento')
    tipodocumento = fields.Selection([], string='Tipo de Documento')
