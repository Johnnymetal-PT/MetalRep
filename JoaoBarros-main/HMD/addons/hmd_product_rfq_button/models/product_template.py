# -*- coding: utf-8 -*-

from ast import literal_eval

from odoo import _, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    rfq_purchase_order_count = fields.Integer(
        string='RFQs',
        compute='_compute_rfq_purchase_order_count',
        compute_sudo=True,
        readonly=True,
    )

    def _compute_rfq_purchase_order_count(self):
        if not self.ids:
            for template in self:
                template.rfq_purchase_order_count = 0
            return

        query = """
            SELECT pp.product_tmpl_id, COUNT(DISTINCT pol.order_id)
            FROM purchase_order_line AS pol
            JOIN product_product AS pp ON pol.product_id = pp.id
            WHERE pp.product_tmpl_id IN %s
            GROUP BY pp.product_tmpl_id
        """
        self.env.cr.execute(query, [tuple(self.ids)])
        count_by_template = dict(self.env.cr.fetchall())
        for template in self:
            template.rfq_purchase_order_count = count_by_template.get(template.id, 0)

    def action_view_rfq_purchase_orders(self):
        self.ensure_one()
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        product_ids = self.product_variant_ids.ids or self.env['product.product'].search([
            ('product_tmpl_id', '=', self.id)
        ]).ids
        if product_ids:
            action['domain'] = [('order_line.product_id', 'in', product_ids)]
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
