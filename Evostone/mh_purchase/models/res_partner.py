from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    container_max_weight = fields.Float(
        string='Cap. Máxima por Contentor (KG)',
        help='Capacidade máxima permitida de carregamento em KG por contentor',
        digits=(16, 2),
        default=0.0
    )
