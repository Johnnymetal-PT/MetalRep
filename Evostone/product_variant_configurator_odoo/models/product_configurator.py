# Copyright 2015 Oihane Crucelaegui - AvanzOSC
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2016 ACSONE SA/NV
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3

import logging

from odoo import _, api, exceptions, fields, models
from odoo.osv.expression import TRUE_DOMAIN

_logger = logging.getLogger(__name__)


class ProductConfigurator(models.AbstractModel):
    _name = "product.configurator"
    _description = "Product Configurator"
    _partner_id_field = "partner_id"

    product_tmpl_id = fields.Many2one(
        string="Product Template", comodel_name="product.template", auto_join=True
    )
    product_attribute_ids = fields.One2many(
        comodel_name="product.configurator.attribute",
        domain=lambda self: [("owner_model", "=", self._name)],
        inverse_name="owner_id",
        string="Product attributes",
        copy=True,
    )
    price_extra = fields.Float(
        compute="_compute_price_extra",
        digits="Product Price",
        help="Price Extra: Extra price for the variant with the currently "
        "selected attributes values on sale price. eg. 200 price extra, "
        "1000 + 200 = 1200.",
    )
    product_id = fields.Many2one(
        string="Product Variant", comodel_name="product.product"
    )
    product_id_configurator_domain = fields.Binary(
        compute="_compute_product_id_configurator_domain",
        readonly=True,
        store=False,
    )
    can_create_product = fields.Boolean(compute="_compute_can_be_created")
    create_product_variant = fields.Boolean(string="Create product now!")

    @api.depends("product_attribute_ids", "product_attribute_ids.price_extra")
    def _compute_price_extra(self):
        for rec in self:
            rec.price_extra = sum(rec.mapped("product_attribute_ids.price_extra"))

    @api.depends(
        "product_attribute_ids", "product_attribute_ids.value_id", "product_id"
    )
    def _compute_can_be_created(self):
        for rec in self:
            if rec.product_id or not rec.product_tmpl_id:
                rec.can_create_product = False
                continue
            rec.can_create_product = not bool(
                len(rec.product_tmpl_id.attribute_line_ids.mapped("attribute_id"))
                - len(list(filter(None, rec.product_attribute_ids.mapped("value_id"))))
            )

    @api.depends("product_tmpl_id", "product_attribute_ids")
    def _compute_product_id_configurator_domain(self):
        product_obj = self.env["product.product"]
        for rec in self:
            if not rec.product_tmpl_id._origin:
                rec.product_id_configurator_domain = TRUE_DOMAIN
            else:
                domain, _cont = product_obj._build_attributes_domain(
                    rec.product_tmpl_id, rec.product_attribute_ids
                )
                rec.product_id_configurator_domain = domain

    def _set_product_tmpl_attributes(self):
        self.ensure_one()
        if self.product_tmpl_id:
            attribute_lines = self.product_attribute_ids.browse([])
            for attribute_line in self.product_tmpl_id.attribute_line_ids:
                attribute_lines += attribute_lines.new(
                    {
                        "attribute_id": attribute_line.attribute_id.ids[0],
                        "product_tmpl_id": self.product_tmpl_id.ids[0],
                        "owner_model": self._name,
                        "owner_id": self.id,
                    }
                )
            self.product_attribute_ids = attribute_lines

    def _set_product_attributes(self):
        self.ensure_one()
        if self.product_id:
            attribute_lines = self.product_attribute_ids.browse([])
            for vals in self.product_id._get_product_attributes_values_dict():
                vals["product_tmpl_id"] = self.product_id.product_tmpl_id
                vals["owner_model"] = self._name
                vals["owner_id"] = self.id
                attribute_lines += attribute_lines.new(vals)
            self.product_attribute_ids = attribute_lines

    @api.onchange("product_tmpl_id")
    def onchange_product_tmpl_id(self):
        self.ensure_one()
        if not self.product_tmpl_id._origin:
            self.product_id = False
        else:
            self._set_product_tmpl_attributes()
            if not self.product_id._origin:
                products = self.product_tmpl_id.product_variant_ids
                if products:
                    self.product_id = products[0]

    @api.onchange("product_id")
    def onchange_product_id(self):
        self.ensure_one()
        if self.product_id._origin:
            if (
                self.product_tmpl_id._origin
                and self.product_tmpl_id != self.product_id.product_tmpl_id
            ):
                self.product_tmpl_id = self.product_id.product_tmpl_id
            self._set_product_attributes()

    @api.onchange("product_attribute_ids")
    def onchange_product_attribute_ids(self):
        self.ensure_one()
        if self.product_attribute_ids._origin:
            product_obj = self.env["product.product"]
            domain, cont = product_obj._build_attributes_domain(
                self.product_tmpl_id, self.product_attribute_ids
            )
            if cont:
                products = product_obj.search(domain, limit=1)
                if products:
                    self.product_id = products[0]

    @api.onchange("create_product_variant")
    def onchange_create_product_variant(self):
        if self.create_product_variant and self.can_create_product:
            product_value_ids = self.product_attribute_ids.mapped(
                "product_template_value_id"
            )
            if product_value_ids:
                self.product_id = self.product_tmpl_id._get_variant_for_combination(
                    product_value_ids
                )
                if not self.product_id:
                    self.product_id = self.product_tmpl_id._create_product_variant(
                        product_value_ids
                    )
            self.create_product_variant = False

    def create_variant_if_needed(self):
        self.ensure_one()
        if self.can_create_product:
            product_value_ids = self.product_attribute_ids.mapped(
                "product_template_value_id"
            )
            if product_value_ids:
                self.product_id = self.product_tmpl_id._get_variant_for_combination(
                    product_value_ids
                )
                if not self.product_id:
                    self.product_id = self.product_tmpl_id._create_product_variant(
                        product_value_ids
                    )
        if not self.product_id:
            _logger.warning("Product not created for %s", self._name)