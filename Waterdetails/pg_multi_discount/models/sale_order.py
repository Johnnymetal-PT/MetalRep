from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    sh_show_multi_disc = fields.Boolean(
        string="Show multi-discount on PDF report",
        default=True,
    )


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    sh_multi_discount = fields.Char(string="Multi Discount %")
    sh_discount_amount = fields.Float(string="Discounted Unit Value", digits='Product Price')
    sh_discount_price_unit = fields.Float(string="Unit Total", readonly=True, digits='Product Price')
    sh_discounted_total_amount = fields.Float(string="Total Discounted Value", digits='Product Price')
    dis_bool = fields.Boolean(compute="_compute_dis_bool", default=True)

    def _compute_dis_bool(self):
        has_group = self.env.user.has_group("pg_multi_discount.group_sale_multi_discount_security")
        for rec in self:
            rec.dis_bool = not has_group

    @api.model
    def _get_multi_discount_values(self, price_unit, quantity, multi_discount):
        values = {
            "sh_discount_price_unit": price_unit,
            "sh_discount_amount": 0.0,
            "sh_discounted_total_amount": 0.0,
            "discount": 0.0,
        }
        if not price_unit or not multi_discount:
            return values

        discount_price_unit = price_unit
        for value in multi_discount.split("+"):
            value = value.strip()
            if not value:
                continue
            try:
                float_value = float(value)
            except ValueError:
                continue
            discount_price = (discount_price_unit * float_value) / 100.0
            discount_price_unit -= discount_price

        discount_amount = price_unit - discount_price_unit
        values.update({
            "sh_discount_price_unit": discount_price_unit,
            "sh_discount_amount": discount_amount,
            "discount": (discount_amount / price_unit) * 100.0 if price_unit else 0.0,
            "sh_discounted_total_amount": discount_amount * quantity,
        })
        return values

    @api.onchange("sh_multi_discount", "product_uom_qty", "price_unit")
    def onchange_discount_percentage(self):
        for rec in self:
            discount_vals = rec._get_multi_discount_values(
                rec.price_unit,
                rec.product_uom_qty,
                rec.sh_multi_discount,
            )
            # Don't overwrite discount when sh_multi_discount was already empty
            # and is still empty — the onchange was triggered by price_unit or
            # product_uom_qty, not by the user clearing a multi-discount string.
            # Clearing sh_multi_discount intentionally is covered by the case
            # where _origin.sh_multi_discount was non-empty.
            if not rec.sh_multi_discount and not rec._origin.sh_multi_discount:
                discount_vals.pop("discount", None)
            rec.update(discount_vals)

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        res.update({
            "sh_discount_price_unit": self.sh_discount_price_unit,
            "sh_discount_amount": self.sh_discount_amount,
            "sh_discounted_total_amount": self.sh_discounted_total_amount,
            "sh_multi_discount": self.sh_multi_discount,
        })
        return res

    @api.model_create_multi
    def create(self, vals_list):
        new_vals_list = []
        for vals in vals_list:
            vals = vals.copy()
            vals.update(self._get_multi_discount_values(
                vals.get("price_unit", 0.0),
                vals.get("product_uom_qty", 0.0),
                vals.get("sh_multi_discount"),
            ))
            new_vals_list.append(vals)
        return super().create(new_vals_list)

    def write(self, vals):
        if not ({"sh_multi_discount", "product_uom_qty", "price_unit"} & vals.keys()):
            return super().write(vals)

        for rec in self:
            rec_vals = vals.copy()
            effective_multi_discount = rec_vals.get("sh_multi_discount", rec.sh_multi_discount)
            discount_vals = rec._get_multi_discount_values(
                rec_vals.get("price_unit", rec.price_unit),
                rec_vals.get("product_uom_qty", rec.product_uom_qty),
                effective_multi_discount,
            )
            # Only propagate discount=0 when sh_multi_discount is actively involved:
            # either it is non-empty (has a value to apply) or it is explicitly
            # being set in this write (including being cleared to "").
            # When the write was triggered by price_unit or qty only, and there
            # is no multi-discount on the record, preserve the existing discount.
            if not effective_multi_discount and "sh_multi_discount" not in vals:
                discount_vals.pop("discount", None)
            rec_vals.update(discount_vals)
            super(SaleOrderLine, rec).write(rec_vals)
        return True
