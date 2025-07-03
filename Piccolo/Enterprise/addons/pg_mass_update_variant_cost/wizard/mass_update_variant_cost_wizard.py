from odoo import fields, models


class MassUpdateVariantCost(models.TransientModel):
    _name = 'mass.update.variant.cost.wizard'

    cost = fields.Float(string='Cost')

    def update_product_cost(self):
        if self._context.get("active_ids"):
            product_id = self.env["product.product"].browse(self._context.get("active_ids"))
            product_id.write({"standard_price": self.cost})
