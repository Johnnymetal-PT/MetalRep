# -*- coding: UTF-8 -*-
# Part of Softhealer Technologies.

import logging
import traceback

from odoo.exceptions import UserError

from odoo import models,_, fields, api

_logger = logging.getLogger(__name__)


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
            trigger_fields = {'sh_multi_discount', 'product_uom_qty', 'price_unit'}
            has_changed_trigger = any(
                field_name in rec_vals and rec_vals[field_name] != rec[field_name]
                for field_name in trigger_fields
            )
            is_editable_order = rec.order_id.state in ('draft', 'sent')
            self._pg_log_multi_discount_write_debug(
                rec=rec,
                incoming_vals=vals,
                effective_vals=rec_vals,
                multi_discount=multi_discount,
                has_changed_trigger=has_changed_trigger,
            )
            if multi_discount and has_changed_trigger and is_editable_order:
                price_unit = rec_vals.get('price_unit', rec.price_unit)
                qty = rec_vals.get('product_uom_qty', rec.product_uom_qty)
                rec_vals.update(rec._get_multi_discount_values(price_unit, qty, multi_discount))
                self._pg_log_multi_discount_write_debug(
                    rec=rec,
                    incoming_vals=vals,
                    effective_vals=rec_vals,
                    multi_discount=multi_discount,
                    has_changed_trigger=has_changed_trigger,
                    recompute_applied=True,
                )
            super(ShSaleOrderLine, rec).write(rec_vals)
        return True

    def _pg_log_multi_discount_write_debug(
        self,
        rec,
        incoming_vals,
        effective_vals,
        multi_discount,
        has_changed_trigger,
        recompute_applied=False,
    ):
        # Focus logs on non-draft orders where certification restrictions can apply.
        if rec.order_id.state in ('draft', 'sent', 'cancel'):
            return

        trigger_snapshot = {
            field_name: {
                'incoming': incoming_vals.get(field_name, '<missing>'),
                'effective': effective_vals.get(field_name, '<missing>'),
                'current': rec[field_name],
            }
            for field_name in ('sh_multi_discount', 'product_uom_qty', 'price_unit')
        }
        context_snapshot = {
            key: self.env.context.get(key)
            for key in (
                'active_model',
                'active_id',
                'active_ids',
                'mail_create_nolog',
                'mail_post_autofollow',
                'tracking_disable',
                'params',
            )
            if key in self.env.context
        }
        stack_preview = " > ".join(
            f"{frame.name}:{frame.lineno}"
            for frame in traceback.extract_stack(limit=8)[:-1]
        )

        _logger.warning(
            "[PG_MULTI_DISCOUNT][WRITE_DEBUG] "
            "line_id=%s order_id=%s order_name=%s order_state=%s "
            "incoming_keys=%s incoming_vals=%s effective_keys=%s effective_vals=%s "
            "multi_discount=%s has_changed_trigger=%s recompute_applied=%s "
            "trigger_snapshot=%s context=%s stack=%s",
            rec.id,
            rec.order_id.id,
            rec.order_id.name,
            rec.order_id.state,
            sorted(incoming_vals.keys()),
            incoming_vals,
            sorted(effective_vals.keys()),
            effective_vals,
            multi_discount,
            has_changed_trigger,
            recompute_applied,
            trigger_snapshot,
            context_snapshot,
            stack_preview,
        )
    

'''class SaleOrderOption(models.Model):
    _inherit = 'sale.order.option'

    discount2 = fields.Float(string="Discount 2 (%)", default=0.0)
    discount3 = fields.Float(string="Discount 3 (%)", default=0.0)
'''

