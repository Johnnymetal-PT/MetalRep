# Copyright 2025 MH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    discount2 = fields.Float(
        string="Desc. 2 %",
        digits="Discount",
        default=0.0,
    )
    discount3 = fields.Float(
        string="Desc. 3 %",
        digits="Discount",
        default=0.0,
    )
    discount4 = fields.Float(
        string="Desc. 4 %",
        digits="Discount",
        default=0.0,
    )
    discounting_type = fields.Selection(
        selection=[("additive", "Additive"), ("multiplicative", "Multiplicative")],
        default="multiplicative",
        required=True,
        help="Specifies whether discounts should be additive "
        "or multiplicative.\nAdditive discounts are summed first and "
        "then applied.\nMultiplicative discounts are applied sequentially.\n"
        "Multiplicative discounts are default",
    )

    def _get_final_discount(self):
        self.ensure_one()
        if self.discounting_type == "additive":
            return self._additive_discount()
        elif self.discounting_type == "multiplicative":
            return self._multiplicative_discount()
        else:
            raise ValidationError(
                _("Sale order line %(name)s has unknown discounting type %(disc_type)s")
                % {"name": self.name, "disc_type": self.discounting_type}
            )

    def _additive_discount(self):
        self.ensure_one()
        discount = sum(self[x] or 0.0 for x in self._discount_fields())
        if discount <= 0:
            return 0
        elif discount >= 100:
            return 100
        return discount

    def _multiplicative_discount(self):
        self.ensure_one()
        discounts = [1 - (self[x] or 0.0) / 100 for x in self._discount_fields()]
        final_discount = 1
        for discount in discounts:
            final_discount *= discount
        result = 100 - final_discount * 100
        dp = self.env.ref("product.decimal_discount").precision_get("Discount")
        return round(result, dp)

    @api.model
    def _discount_fields(self):
        return ["discount", "discount2", "discount3", "discount4"]

    @api.depends("discount2", "discount3", "discount4", "discounting_type",
                 "product_uom_qty", "price_unit", "tax_id")
    def _compute_amount(self):
        return super()._compute_amount()

    def _prepare_base_line_for_taxes_computation(self, **kwargs):
        """Override to inject aggregated discount into tax calculation"""
        res = super()._prepare_base_line_for_taxes_computation(**kwargs)
        # Replace discount with aggregated discount
        res['discount'] = self._get_final_discount()
        return res

    _sql_constraints = [
        (
            "discount2_limit",
            "CHECK (discount2 <= 100.0)",
            "Discount 2 must be lower or equal than 100%.",
        ),
        (
            "discount3_limit",
            "CHECK (discount3 <= 100.0)",
            "Discount 3 must be lower or equal than 100%.",
        ),
        (
            "discount4_limit",
            "CHECK (discount4 <= 100.0)",
            "Discount 4 must be lower or equal than 100%.",
        ),
    ]

    def _prepare_invoice_line(self, **kwargs):
        """
        Inherit this method to bring
        more discount fields to the invoice lines
        """
        res = super()._prepare_invoice_line(**kwargs)
        res.update({
            "discount2": self.discount2,
            "discount3": self.discount3,
            "discount4": self.discount4,
            "discounting_type": self.discounting_type,
        })
        return res

    def _convert_to_tax_base_line_dict(self):
        self.ensure_one()
        discount = self._get_final_discount()
        return self.env["account.tax"]._convert_to_tax_base_line_dict(
            self,
            partner=self.order_id.partner_id,
            currency=self.order_id.currency_id,
            product=self.product_id,
            taxes=self.tax_id,
            price_unit=self.price_unit,
            quantity=self.product_uom_qty,
            discount=discount,
            price_subtotal=self.price_subtotal,
        )
