# Copyright 2015 Oihane Crucelaegui - AvanzOSC
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2016 ACSONE SA/NV
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3

from odoo import api, fields, models


class ProductTemplateAttributeLine(models.Model):
    _inherit = "product.template.attribute.line"

    required = fields.Boolean(
        default=True,
        readonly=True
    )

    _sql_constraints = [
        (
            "product_attribute_uniq",
            "unique(product_tmpl_id, attribute_id)",
            "The attribute already exists for this product",
        )
    ]

    @api.onchange("attribute_id")
    def _onchange_attribute_id_clean_value(self):
        """This is for consistency when changing attribute in the product."""
        self.value_ids = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("value_ids", False) and vals.get("value_ids")[0]:
                if vals.get("value_ids")[0][0] == 6:
                    vals["value_ids"] = vals.get("value_ids")
                elif vals.get("value_ids")[0][0] == 1:
                    vals["value_ids"] = [(4, vals.get("value_ids")[0][1])]
        return super().create(vals_list)