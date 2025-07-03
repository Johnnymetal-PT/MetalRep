from odoo import models


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_product_product(self):
        params = super()._loader_params_product_product()
        fields = params.get('search_params', {}).get('fields', [])
        if 'x_studio_referncia_interna' not in fields:
            fields.append('x_studio_referncia_interna')
        return params
