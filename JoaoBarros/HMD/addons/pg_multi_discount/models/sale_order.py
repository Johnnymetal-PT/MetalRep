# -*- coding: UTF-8 -*-
# Part of Softhealer Technologies.

from odoo.exceptions import UserError

from odoo import models,_, fields, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    sh_show_multi_disc = fields.Boolean(
        string="Show Multi Discount In PDF Report",
        default=True
    )


class ShSaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    sh_multi_discount = fields.Char(string="Multi Discount")
    sh_discount_amount = fields.Float(string="Discount Amount")
    sh_discount_price_unit = fields.Float(string="DUP", readonly=True)
    sh_discounted_total_amount = fields.Float(
        string="Discounted Total Amount"
    )
    dis_bool = fields.Boolean(compute="_compute_dis_bool", default="True")

    def _compute_dis_bool(self):
        for rec in self:
            rec.dis_bool = True
            if self.env.user.has_group('sh_multi_discount.group_sale_multi_discount_security'):
                rec.dis_bool = False

    @api.model
    def _get_multi_discount_values(self, price_unit, quantity, multi_discount):
        values = {
            'sh_discount_price_unit': price_unit,
            'sh_discount_amount': 0.0,
            'sh_discounted_total_amount': 0.0,
        }

        if not price_unit or not multi_discount:
            values['discount'] = 0.0
            return values

        discount_price_unit = price_unit
        for value in multi_discount.split("+"):
            value = value.strip()
            if not value:
                continue
            float_value = float(value)
            discount_price = (discount_price_unit * float_value) / 100
            discount_price_unit -= discount_price

        discount_amount = price_unit - discount_price_unit
        values.update({
            'sh_discount_price_unit': discount_price_unit,
            'sh_discount_amount': discount_amount,
            'discount': (discount_amount / price_unit) * 100 if price_unit else 0.0,
            'sh_discounted_total_amount': discount_amount * quantity,
        })
        return values

    # get Discount Unit price, discount total amount and discount amount and discount percentage based on multi discount
    @api.onchange('sh_multi_discount', 'product_uom_qty', 'price_unit')
    def onchange_discount_percentage(self):
        for rec in self:
            if rec.sh_multi_discount:
                rec.update(rec._get_multi_discount_values(
                    rec.price_unit,
                    rec.product_uom_qty,
                    rec.sh_multi_discount,
                ))


    def _prepare_invoice_line(self, **optional_values):
        res = super(ShSaleOrderLine, self)._prepare_invoice_line(**optional_values)
        res.update({
            'sh_discount_price_unit':self.sh_discount_price_unit,
            'sh_discount_amount':self.sh_discount_amount,
            'sh_discounted_total_amount':self.sh_discounted_total_amount,
            'sh_multi_discount':self.sh_multi_discount
        })
        return res

    @api.model
    def create(self, vals):
        vals = vals.copy()
        if vals.get('sh_multi_discount'):
            price_unit = vals.get('price_unit', 0.0)
            qty = vals.get('product_uom_qty', 0.0)
            discount_vals = self._get_multi_discount_values(
                price_unit,
                qty,
                vals.get('sh_multi_discount'),
            )
            vals.update(discount_vals)

        return super().create(vals)

    def write(self, vals):
        for rec in self:
            rec_vals = vals.copy()
            multi_discount = rec_vals.get('sh_multi_discount', rec.sh_multi_discount)
            if multi_discount and ({'sh_multi_discount', 'product_uom_qty', 'price_unit'} & rec_vals.keys()):
                price_unit = rec_vals.get('price_unit', rec.price_unit)
                qty = rec_vals.get('product_uom_qty', rec.product_uom_qty)
                rec_vals.update(rec._get_multi_discount_values(price_unit, qty, multi_discount))
            super(ShSaleOrderLine, rec).write(rec_vals)
        return True
    

'''class SaleOrderOption(models.Model):
    _inherit = 'sale.order.option'

    discount2 = fields.Float(string="Discount 2 (%)", default=0.0)
    discount3 = fields.Float(string="Discount 3 (%)", default=0.0)
'''