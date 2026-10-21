from odoo import api, fields, models


class ResPartnerGrade(models.Model):
    _inherit = 'res.partner.grade'
    _order = 'pg_min_invoiced desc, sequence, id'

    pg_auto_assign = fields.Boolean(
        string="Atribuir automaticamente",
        default=False,
        help="Se ligado, este escalão entra no cálculo automático por faturação.\n"
             "Escalões desligados só podem ser atribuídos à mão — útil para casos"
             " negociados que não devem seguir a tabela.",
    )
    pg_min_invoiced = fields.Monetary(
        string="Faturação mínima",
        currency_field='pg_currency_id',
        help="Valor de faturação a partir do qual o cliente entra neste escalão."
             " O cliente fica no escalão mais alto cuja faturação mínima já tenha"
             " atingido.",
    )
    pg_currency_id = fields.Many2one(
        comodel_name='res.currency',
        compute='_compute_pg_currency_id',
    )

    @api.depends('company_id')
    def _compute_pg_currency_id(self):
        for grade in self:
            grade.pg_currency_id = (grade.company_id or self.env.company).currency_id
