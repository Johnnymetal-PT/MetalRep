from odoo import models, fields, api


class CustomPayslipLine(models.Model):
    _name = 'custom.payslip.line'
    _description = 'Linha de Folha Personalizada'

    name = fields.Char(string='Nome')
    payslip_id = fields.Many2one('hr.payslip', string='Folha de Pagamento', ondelete='cascade')
    category_id = fields.Many2one('hr.salary.rule.category', string='Categoria da Regra de Salario')
    total = fields.Monetary(string='Total', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', related='payslip_id.company_id.currency_id', readonly=True, store=True)
