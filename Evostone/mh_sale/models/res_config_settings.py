from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_discount_limit = fields.Float(
        string='Limite de Desconto para Usuários (%)',
        default=5.0,
        config_parameter='mh_sale.sale_discount_limit',
        help='Desconto máximo permitido para usuários não-administradores. '
             'Administradores e Gerentes de Vendas não têm limite.'
    )
