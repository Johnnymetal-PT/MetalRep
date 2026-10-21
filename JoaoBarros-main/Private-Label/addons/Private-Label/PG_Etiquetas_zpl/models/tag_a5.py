import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # Button: Imprimir Entregas
    def action_print_zpl_entrega(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Escolher Impressora Etiqueta Entrega',
            'res_model': 'choose.iot.printer.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_picking_id': self.id,
                'default_label_type': 'Entrega',
            }
        }

    # Button: Imprimir Tecidos
    def action_print_zpl_tecido(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Escolher Impressora Etiqueta Tecido',
            'res_model': 'choose.iot.printer.wizard_tecido',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_picking_id': self.id,
                'default_label_type': 'Tecido',
            }
        }
