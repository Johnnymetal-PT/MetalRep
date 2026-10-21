# Copyright 2025 MH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

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
                _("Invoice line %(name)s has unknown discounting type %(disc_type)s")
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

    @api.depends('quantity', 'discount', 'discount2', 'discount3', 'discount4',
                 'discounting_type', 'price_unit', 'tax_ids', 'currency_id')
    def _compute_totals(self):
        return super()._compute_totals()

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
