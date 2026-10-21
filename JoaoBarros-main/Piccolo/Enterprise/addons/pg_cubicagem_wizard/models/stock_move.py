from odoo import models

class StockMove(models.Model):
    _inherit = 'stock.move'

    def open_cubicagem_wizard(self):
        self.ensure_one()
        return {
            'name': 'Cubicagem Wizard',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move.cubicagem.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_move_id': self.id,
            }
        }

