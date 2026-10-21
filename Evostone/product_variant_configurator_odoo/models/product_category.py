# Copyright 2015 Oihane Crucelaegui - AvanzOSC
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2016 ACSONE SA/NV
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3

from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    no_create_variants = fields.Boolean(
        string="Don't create product variants",
        help="If checked, the products of this category won't create "
        "variants automatically.",
    )