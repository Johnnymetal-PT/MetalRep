"""Wizard de impressao do `pg_zpl_tags_sofmovel`.

[POSSIVELMENTE OBSOLETO] Ver substituto `PG_Etiquetas_A5`.
"""
from odoo import models, fields

class LabelWizard(models.TransientModel):
    """Wizard simples para escolher formato e disparar a impressao ZPL."""

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

