from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_feature_progressive_accounts_sale = fields.Boolean(
        string='Contas progressivas dos clientes',
        config_parameter='account_MZ.progressive_accounts_sale'
    )
    enable_feature_progressive_accounts_purchase = fields.Boolean(
        string='Contas progressivas dos fornecedores',
        config_parameter='account_MZ.progressive_accounts_purchase'
    )
