from odoo import models

class StockPicking(models.Model):
    _inherit = 'product.template'

    def action_print_a4_report(self):
        report = self.env['ir.actions.report'].search([('name', '=', 'Etiquetas A4')], limit=1)
        return report.report_action(self)
        
        
        
class StockPicking(models.Model):
    _inherit = 'product.product'

    def action_print_a4_report(self):
        report = self.env['ir.actions.report'].search([('name', '=', 'Etiquetas A4')], limit=1)
        return report.report_action(self)
        
        
        
class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_print_a4_report(self):
        report = self.env['ir.actions.report'].search([('name', '=', 'Etiqueta A4')], limit=1)
        return report.report_action(self)
        
    def action_print_a4_report_mythica(self):
        report = self.env['ir.actions.report'].search([('name', '=', 'Etiqueta Mythica A4')], limit=1)
        return report.report_action(self)

        
from odoo import models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_print_a4_report(self):
        report = self.env['ir.actions.report'].search([
            ('report_name', '=', 'studio_customization.studio_report_docume_93ca904d-bd32-4f00-842d-a202961be350'),
            ('model', '=', 'sale.order'),
        ], limit=1)
        return report.report_action(self)

        
    def action_print_a4_report_mythica(self):
        report = self.env['ir.actions.report'].search([
            ('report_name', '=', 'studio_customization.studio_report_docume_78594e7c-93c4-4f64-841b-8a2622da2b1b'),
            ('model', '=', 'sale.order'),
        ], limit=1)
        return report.report_action(self)

