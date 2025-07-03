from odoo import models, fields, api

class ZPLLabelWizard(models.TransientModel):  # Ensure TransientModel is used
    _name = "zpl.label.wizard"
    _description = "Choose ZPL Label Size"

    label_size = fields.Selection([
        ('produtos', 'Tecidos (55mm x 28mm)'),
        ('jdias', 'J.Dias (55mm x 28mm)'),
        ('acabamento', 'Acabamento/Polimento (55mm x 28mm)'),
    ], string="Label Size", required=True, default='produtos')

    def action_print_zpl2(self):
        """ Generate ZPL label based on selected size """
        stock_picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
        
        if not stock_picking:
            raise ValueError("No stock picking found.")

        return stock_picking.action_print_zpl2(self.label_size)
