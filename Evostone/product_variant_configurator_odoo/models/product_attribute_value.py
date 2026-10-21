# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3

from odoo import api, models


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "name" not in vals and self.env.context.get("product_attribute_value_name"):
                vals["name"] = self.env.context.get("product_attribute_value_name")
        return super().create(vals_list)