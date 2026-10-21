"""Loader params do POS: inclui o campo Studio na lista de campos enviados ao cliente.

Pertence ao modulo `pg_pos_search_ref_interna`. Sem este override, o campo
`x_studio_referncia_interna` nao chega ao bundle do POS e o patch JS nao tem
sobre o que actuar.
"""
from odoo import models


class PosSession(models.Model):
    """Garante que o campo Studio e enviado para o cliente POS."""

    _inherit = 'pos.session'

    def _loader_params_product_product(self):
        params = super()._loader_params_product_product()
        fields = params.get('search_params', {}).get('fields', [])
        # Injeta o campo Studio no payload do POS para pesquisa por referencia.
        if 'x_studio_referncia_interna' not in fields:
            fields.append('x_studio_referncia_interna')
        return params
