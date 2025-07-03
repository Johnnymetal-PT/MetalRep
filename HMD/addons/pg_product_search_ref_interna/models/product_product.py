from odoo import models, api

class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
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
            ref = product.default_code or product.x_studio_referncia_interna or ""
            display_name = f"[{ref}] {name}" if ref else name or "-"
            result.append((product.id, display_name))
        return result
