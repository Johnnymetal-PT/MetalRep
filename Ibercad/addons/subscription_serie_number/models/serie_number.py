from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    serial_number = fields.Char(string='Número de Série', store=True)

    def _prepare_invoice_line(self, **kwargs):
        # Call the super method to handle normal invoice line preparation
        invoice_lines = super(SaleOrderLine, self)._prepare_invoice_line(**kwargs)
        
        # Ensure no interference with price list logic by appending serial_number only if relevant
        if 'serial_number' in self:
            invoice_lines.update({'serial_number': self.serial_number})
        
        return invoice_lines



class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    serial_number = fields.Char(string='Número de Série', store='True')

class AccountMove(models.Model):
    _inherit = 'account.move'

    serial_number = fields.Char(string='Número de Série', store='True')



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    recurring_invoice = fields.Boolean(string="Recurring Invoice", default='True')
    serial_number = fields.Char(string='Número de Série', store='True')
    
