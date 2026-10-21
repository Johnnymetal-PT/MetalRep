from odoo import models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def action_open_qr_scanner(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'open_qr_scanner',
        }

