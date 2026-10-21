from odoo import models, fields

class LabelWizard(models.TransientModel):
    _name = "label.wizard"
    _description = "Assistente de Impressão de Etiquetas"

    quantity = fields.Integer(string="Quantidade", default=1)
    format = fields.Selection([
        ('zpl_price', 'ZPL Labels with price'),
        ('zpl', 'ZPL Labels'),
        # outros formatos...
    ], string="Formato", required=True)

    def action_print_label(self):
        if self.format == 'zpl_price':
            product = self.env['product.product'].browse(self.env.context.get('active_id'))
            product.action_print_zpl_label()
        return {'type': 'ir.actions.act_window_close'}

