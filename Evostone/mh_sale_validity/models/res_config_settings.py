from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auto_cancel_expired_quotations = fields.Boolean(
        string='Cancelar Automaticamente Cotações Expiradas',
        help='Se ativado, o sistema cancelará automaticamente as cotações expiradas. '
             'Caso contrário, apenas adicionará uma notificação nas cotações expiradas.'
    )

    @api.model
    def get_values(self):
        """Buscar valores dos parâmetros de configuração"""
        res = super(ResConfigSettings, self).get_values()

        auto_cancel = self.env['ir.config_parameter'].sudo().get_param(
            'mh_sale_validity.auto_cancel_expired',
            default='False'
        )

        res.update(
            auto_cancel_expired_quotations=(auto_cancel == 'True')
        )

        return res

    def set_values(self):
        """Salvar valores nos parâmetros de configuração"""
        super(ResConfigSettings, self).set_values()

        self.env['ir.config_parameter'].sudo().set_param(
            'mh_sale_validity.auto_cancel_expired',
            str(self.auto_cancel_expired_quotations)
        )
