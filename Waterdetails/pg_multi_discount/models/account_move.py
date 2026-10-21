from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    sh_show_multi_disc = fields.Boolean(
        string="Show multi-discount on PDF report",
        default=True,
    )


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    sh_multi_discount = fields.Char(string="Multi Discount %")
    sh_discount_amount = fields.Float(string="Discounted Unit Value", digits='Product Price')
    sh_discount_price_unit = fields.Float(string="Unit Total", readonly=True, digits='Product Price')
    sh_discounted_total_amount = fields.Float(string="Total Discounted Value", digits='Product Price')
    dis_bool = fields.Boolean(compute="_compute_dis_bool", default=True)

    def _compute_dis_bool(self):
        has_group = self.env.user.has_group("pg_multi_discount.group_account_multi_discount_security")
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
            discount_price_unit -= (discount_price_unit * float_value) / 100.0

        discount_amount = price_unit - discount_price_unit
        values.update({
            "sh_discount_price_unit": discount_price_unit,
            "sh_discount_amount": discount_amount,
            "discount": (discount_amount / price_unit) * 100.0 if price_unit else 0.0,
            "sh_discounted_total_amount": discount_amount * quantity,
        })
        return values

    @api.onchange("sh_multi_discount", "quantity", "price_unit")
    def onchange_discount_percentage(self):
        for rec in self:
            rec.update(rec._get_multi_discount_values(
                rec.price_unit,
                rec.quantity,
                rec.sh_multi_discount,
            ))

    @api.model_create_multi
    def create(self, vals_list):
        new_vals_list = []
        for vals in vals_list:
            vals = vals.copy()
            vals.update(self._get_multi_discount_values(
                vals.get("price_unit", 0.0),
                vals.get("quantity", 0.0),
                vals.get("sh_multi_discount"),
            ))
            new_vals_list.append(vals)
        return super().create(new_vals_list)

    def write(self, vals):
        if not ({"sh_multi_discount", "quantity", "price_unit"} & vals.keys()):
            return super().write(vals)

        for rec in self:
            rec_vals = vals.copy()
            rec_vals.update(rec._get_multi_discount_values(
                rec_vals.get("price_unit", rec.price_unit),
                rec_vals.get("quantity", rec.quantity),
                rec_vals.get("sh_multi_discount", rec.sh_multi_discount),
            ))
            super(AccountMoveLine, rec).write(rec_vals)
        return True
