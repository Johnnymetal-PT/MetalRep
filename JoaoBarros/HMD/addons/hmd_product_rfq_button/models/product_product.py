# -*- coding: utf-8 -*-

from ast import literal_eval

from odoo import _, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    rfq_variant_purchase_order_count = fields.Integer(
        string='RFQs',
        compute='_compute_rfq_variant_purchase_order_count',
        compute_sudo=True,
        readonly=True,
    )

    def _compute_rfq_variant_purchase_order_count(self):
        purchase_order_line = self.env['purchase.order.line'].sudo()
        grouped_data = purchase_order_line.read_group(
            domain=[('product_id', 'in', self.ids)],
            fields=['product_id', 'order_id:count_distinct'],
            groupby=['product_id'],
        ) if self.ids else []
        count_by_product = {
            data['product_id'][0]: data.get('order_id_count_distinct', 0)
            for data in grouped_data
        }
        for product in self:
            product.rfq_variant_purchase_order_count = count_by_product.get(product.id, 0)

    def action_view_rfq_purchase_orders(self):
        self.ensure_one()
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        if self.id:
            action['domain'] = [('order_line.product_id', '=', self.id)]
        else:
            action['domain'] = [('id', '=', False)]
        action['name'] = _('RFQs')
        context = action.get('context')
        if isinstance(context, str):
            context = literal_eval(context)
        sanitized_context = dict(context or {})
        keys_to_remove = [key for key in sanitized_context if key.startswith('search_default_')]
        for key in keys_to_remove:
            sanitized_context.pop(key, None)
        action['context'] = sanitized_context
        return action
