from odoo import models, fields


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    custom_line_ids = fields.One2many('custom.payslip.line', 'payslip_id', string='Custom Payslip Lines')
