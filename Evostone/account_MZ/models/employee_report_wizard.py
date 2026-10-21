from odoo import models, fields, api


class EmployeeReportWizard(models.TransientModel):
    _name = 'employee.report.wizard'
    _description = 'Relatório de Funcionários'

