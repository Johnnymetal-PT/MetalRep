"""Mapeamento de categorias fornecedor -> Odoo + regras de margem por categoria."""

from odoo import fields, models


class HiperSyncCategoryMap(models.Model):
    """Liga uma categoria do feed do fornecedor a uma categoria interna/publica.

    Tambem transporta as regras comerciais (custo de envio, margens, desconto
    de origem) que ``hiper.sync.vendor._compute_price_for_row`` aplica para
    obter o preco final. A unicidade ``(vendor_id, kind, origin_name)`` garante
    que cada categoria do fornecedor so tem uma regra activa.
    """

    _name = "hiper.sync.category.map"
    _description = "Hiper Supplier Category Map"
    _order = "vendor_id, origin_name, id"

    vendor_id = fields.Many2one(
        "hiper.sync.vendor",
        required=True,
        ondelete="cascade",
        index=True,
        help="Supplier this mapping belongs to.",
    )
    kind = fields.Selection(
        [("category", "Category"), ("sub_category", "Sub Category")],
        required=True,
        default="category",
        help="Which source field from the supplier feed this rule applies to.",
    )
    origin_name = fields.Char(
        required=True,
        index=True,
        help="Exact category or subcategory name received from the supplier feed.",
    )
    target_categ_id = fields.Many2one(
        "product.category",
        string="Internal Category",
        help="Odoo internal category to assign when this supplier category matches.",
    )
    target_public_categ_id = fields.Many2one(
        "product.public.category",
        string="Website Category",
        help="Odoo website category to assign when this supplier category matches.",
    )
    shipping_cost = fields.Float(
        help="Fixed shipping cost added into the selling price calculation for this mapped category."
    )
    margin_percent = fields.Float(
        help="Main margin percentage applied to the supplier cost for this mapped category."
    )
    extra_margin_percent = fields.Float(
        help="Additional margin percentage stacked on top of the main margin."
    )
    origin_discount_percent = fields.Float(
        help="Supplier-side discount percentage removed from the original cost before final price calculation."
    )
    active = fields.Boolean(default=True, help="Disable the rule without deleting it.")

    _sql_constraints = [
        (
            "hiper_sync_category_map_unique",
            "unique(vendor_id, kind, origin_name)",
            "Each origin category can only be mapped once per supplier.",
        )
    ]
