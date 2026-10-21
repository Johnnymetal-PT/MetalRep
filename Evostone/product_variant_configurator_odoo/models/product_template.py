# Copyright 2015 Oihane Crucelaegui - AvanzOSC
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2016 ACSONE SA/NV
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3

from odoo import _, api, fields, models
from odoo.tools import config


class ProductTemplate(models.Model):
    _inherit = "product.template"

    no_create_variants = fields.Selection(
        [
            ("yes", "Don't create them automatically"),
            ("no", "Use Odoo's default variant management"),
            ("empty", "Use the category value"),
        ],
        string="Variant creation",
        required=True,
        readonly=True,
        default="yes",
        help="This selection defines if variants for all attribute "
        "combinations are going to be created automatically at saving "
        "time.",
    )

    @api.onchange("no_create_variants")
    def onchange_no_create_variants(self):
        if (
            self.no_create_variants in ["no", "empty"]
            and self._origin.no_create_variants
        ):
            return {
                "warning": {
                    "title": _("Change warning!"),
                    "message": _(
                        "Changing this parameter may cause"
                        " automatic variants creation"
                    ),
                }
            }

    @api.model_create_multi
    def create(self, vals_list):
        if "product_name" in self.env.context:
            for vals in vals_list:
                vals["name"] = self.env.context["product_name"]
        return super().create(vals_list)

    def write(self, values):
        res = super().write(values)
        if "no_create_variants" in values:
            self._create_variant_ids()
        return res

    def _get_product_attributes_dict(self):
        return self.attribute_line_ids.mapped(
            lambda x: {"attribute_id": x.attribute_id.id}
        )

    def _create_variant_ids(self):
        obj = self.with_context(creating_variants=True)
        if config["test_enable"] and not self.env.context.get("check_variant_creation"):
            return super()._create_variant_ids()
        for tmpl in obj:
            if (
                (
                    tmpl.no_create_variants == "empty"
                    and not tmpl.categ_id.no_create_variants
                )
                or tmpl.no_create_variants == "no"
                or not tmpl.attribute_line_ids
            ):
                super(ProductTemplate, tmpl)._create_variant_ids()
        return True