from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    # Campo Many2many para compartilhar plano de contas entre empresas
    chart_account_ids = fields.Many2many(
        'company.chart.account',
        'company_chart_account_rel',
        'company_id',
        'account_id',
        string='Plano de Contas',
        help='Plano de contas compartilhado desta empresa'
    )