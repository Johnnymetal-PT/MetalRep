# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PgMrpDefaultWorkorder(models.Model):
    _name = 'pg.mrp.default.workorder'
    _description = 'Centro de Trabalho por Defeito (Ordens de Fabrico)'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sequência', default=10)
    name = fields.Char(string='Operação', required=True)
    workcenter_id = fields.Many2one(
        'mrp.workcenter', string='Centro de Trabalho',
        required=True)
    duration_expected = fields.Float(
        string='Duração Prevista',
        help='Duração prevista (em minutos) atribuída à Ordem de Trabalho criada.')
    company_id = fields.Many2one(
        'res.company', string='Empresa',
        default=lambda self: self.env.company,
        help='Deixar vazio para aplicar a todas as empresas.')

    @api.onchange('workcenter_id')
    def _onchange_workcenter_id(self):
        # Conveniência: usar o nome do centro de trabalho como nome da operação por defeito.
        for default in self:
            if default.workcenter_id and not default.name:
                default.name = default.workcenter_id.name
