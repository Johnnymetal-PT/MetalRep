"""Estende `name_search` e `name_get` de `product.product` com a referencia Studio.

Pertence ao modulo `pg_product_search_ref_interna`. O campo
`x_studio_referncia_interna` e o codigo interno de produto (Studio); este
modulo torna-o pesquisavel em Many2one e mostra-o como prefixo no
display name.
"""
from odoo import models, api

class ProductProduct(models.Model):
    """Permite pesquisar produtos por referencia interna Studio."""

    _inherit = 'product.product'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        # OR sobre nome, default_code e referencia Studio.
        domain = ['|', '|',
                  ('name', operator, name),
                  ('default_code', operator, name),
                  ('x_studio_referncia_interna', operator, name)]
        products = self.search(domain + args, limit=limit)
        return products.name_get()

    def name_get(self):
        result = []
        for product in self:
            name = product.name or ""
            # Prioriza default_code; se vazio, usa referencia Studio.
            ref = product.default_code or product.x_studio_referncia_interna or ""
            display_name = f"[{ref}] {name}" if ref else name or "-"
            result.append((product.id, display_name))
        return result
