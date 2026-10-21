"""Wizard de escolha do template ZPL a imprimir.

Picking e recuperado via ``context['active_id']`` (passado por
``stock.picking.action_open_zpl_wizard``).
"""
from odoo import models, fields


class ZPLLabelWizard(models.TransientModel):
    _name = "zpl.label.wizard"
    _description = "Choose ZPL Label Size"

    # Cada chave mapeia para um template em
    # pg_zpl_tags_2/models/zpl_tags.py:zpl_templates.
    label_size = fields.Selection(
        [
            ('produtos', 'Tecidos (55mm x 28mm)'),
            ('jdias', 'J.Dias (55mm x 28mm)'),
            ('acabamento', 'Acabamento/Polimento (55mm x 28mm)'),
        ],
        string="Label Size",
        required=True,
        default='produtos',
    )

    def action_print_zpl2(self):
        """Delega a impressao no picking ativo passado por contexto."""
        stock_picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))

        if not stock_picking:
            raise ValueError("No stock picking found.")

        return stock_picking.action_print_zpl2(self.label_size)
