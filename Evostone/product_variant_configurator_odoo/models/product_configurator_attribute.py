# Copyright 2015 Oihane Crucelaegui - AvanzOSC
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2016 ACSONE SA/NV
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3

from odoo import api, fields, models


class ProductConfiguratorAttribute(models.Model):
    _name = "product.configurator.attribute"
    _description = "Product Configurator Attribute"
    _rec_name = "attribute_id"
    _order = "sequence, attribute_id, value_id, id"

    owner_id = fields.Many2oneReference(
        string="Owner", 
        required=True, 
        index=True, 
        model_field="owner_model"
    )
    owner_model = fields.Char(required=True)
    product_tmpl_id = fields.Many2one(
        comodel_name="product.template", 
        string="Product Template", 
        required=True
    )
    attribute_id = fields.Many2one(string="Attribute", comodel_name="product.attribute", readonly=True)
    value_id = fields.Many2one(
        comodel_name="product.attribute.value",
        domain="[('id', 'in', possible_value_ids)]",
        string="Value",
    )
    price_extra = fields.Float(
        compute="_compute_price_extra",
        default=0.0,
        digits="Product Price",
        string="Attribute price extra",
        help="Price Extra: Extra price for the variant with this attribute "
        "value on sale price. eg. 200 price extra, 1000 + 200 = 1200.",
    )
    product_template_value_id = fields.Many2one(
        string="Product Template Value",
        comodel_name="product.template.attribute.value",
        compute="_compute_product_template_value_id",
    )
    possible_value_ids = fields.Many2many(
        comodel_name="product.template.attribute.value",
        compute="_compute_possible_value_ids",
        string="Possible Values",
    )
    sequence = fields.Integer(related="attribute_id.sequence", store=True)

    @api.depends("product_tmpl_id", "attribute_id", "value_id", "owner_id", "owner_model")
    def _compute_product_template_value_id(self):
        for record in self:
            if record.attribute_id and record.value_id and record.product_tmpl_id:
                record.product_template_value_id = (
                    self.env["product.template.attribute.value"].search(
                        [
                            ("product_tmpl_id", "=", record.product_tmpl_id.id),
                            ("attribute_id", "=", record.attribute_id.id),
                            ("product_attribute_value_id", "=", record.value_id.id),
                        ],
                        limit=1,
                    )
                )
            else:
                record.product_template_value_id = False

    @api.depends("product_tmpl_id", "attribute_id", "value_id", "owner_id", "owner_model")
    def _compute_price_extra(self):
        for record in self:
            if record.product_template_value_id:
                record.price_extra = record.product_template_value_id.price_extra
            else:
                record.price_extra = 0.0

    @api.depends("attribute_id", "product_tmpl_id")
    def _compute_possible_value_ids(self):
        for record in self:
            if record.product_tmpl_id and record.attribute_id:
                record.possible_value_ids = (
                    self.env["product.template.attribute.value"].search(
                        [
                            ("product_tmpl_id", "=", record.product_tmpl_id.id),
                            ("attribute_id", "=", record.attribute_id.id),
                        ]
                    )
                )
            else:
                record.possible_value_ids = False

    @api.onchange("value_id")
    def onchange_value_id(self):
        self._compute_product_template_value_id()
        self._compute_price_extra()