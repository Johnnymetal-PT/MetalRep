from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    zebra_print_server_url = fields.Char(
        string='Zebra Print Server URL',
        config_parameter='mh_stone_reports.zebra_print_server_url',
        help='URL publica do Zebra Print Server (preenchido automaticamente pelo print agent)',
    )
