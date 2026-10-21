# -*- coding: UTF-8 -*-
# Part of Softhealer Technologies.
"""Desconto multiplo em linhas de compra com propagacao para vendor bills.

Replica a mesma formula em cascata do modulo de vendas para manter consistencia
entre procurement e contabilizacao.
"""

from odoo import models, fields, api


class ShPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    sh_show_multi_disc = fields.Boolean(
        string="Show Multi Discount In PDF Report",
        default=True
    )


class ShPurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    sh_multi_discount = fields.Char(string="Multi Discount")
    sh_discount_amount = fields.Float(string="Discount Amount")
    sh_discount_price_unit = fields.Float(string="DUP")
    sh_discounted_total_amount = fields.Float(
        string="Discounted Total Amount"
    )
    dis_bool = fields.Boolean(compute="_compute_dis_bool", default="True")

    def _compute_dis_bool(self):
        # Campo de controlo visual: quem nao tem grupo apropriado nao edita.
        for rec in self:
            rec.dis_bool = True
            if self.env.user.has_group('sh_multi_discount.group_purchase_multi_discount_security'):
                rec.dis_bool = False


    # get Discount Unit price, discount total amount and discount amount and discount percentage based on multi discount
    @api.onchange('sh_multi_discount', 'product_qty', 'price_unit')
    def onchange_discount_percentage(self):
        # Formato esperado: "10+5+2" (percentagens em cascata).
        if self:
            for rec in self:
                if rec.sh_multi_discount:
                    discount_list = list(rec.sh_multi_discount.split("+"))
                    price_list = []
                    price_list.append(float(rec.price_unit))
                    price_unit = rec.price_unit
                    if price_unit > 0:
                        for value in discount_list:
                            if value:
                                float_value = float(value)
                                discount_price = (price_unit * float_value) / (100)
                                price_unit = price_unit - discount_price
                                rec.sh_discount_price_unit = price_unit
                                rec.sh_discount_amount = price_list[0] - rec.sh_discount_price_unit
                                rec.discount = (rec.sh_discount_amount / price_list[0]) * 100
                                rec.sh_discounted_total_amount = rec.sh_discount_amount * rec.product_qty
                            else:
                               rec.sh_multi_discount = rec.sh_multi_discount[:-1]
                    
    def _prepare_account_move_line(self, move=False):
        # Leva os campos de desconto para vendor bill.
        res = super(ShPurchaseOrderLine, self)._prepare_account_move_line(move)
        res.update({
            'sh_discount_price_unit':self.sh_discount_price_unit,
            'sh_discount_amount':self.sh_discount_amount,
            'sh_discounted_total_amount':self.sh_discounted_total_amount,
            'sh_multi_discount':self.sh_multi_discount
        })

        return res
