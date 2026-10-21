from odoo import models, fields


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    active_rule = fields.Boolean(string='Regra Ativa', default=True)
