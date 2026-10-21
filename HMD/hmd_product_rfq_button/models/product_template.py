# -*- coding: utf-8 -*-
"""Botao smart "RFQs" em `product.template`.

Conta TODAS as `purchase.order` (em qualquer estado, incluindo
cancelado) ligadas a este template via `purchase.order.line.product_id`.

Ver `__manifest__.py` para o guia completo.
"""

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

        # SQL raw: mais rapido que read_group em batches grandes. Conta
        # POs distintas (DISTINCT order_id) cujas linhas tenham produto
        # ligado a um dos templates. Sem filtro de estado - intencional.
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
        action = self.env['ir.actions.actions']._for_xml_id('purchase.purchase_rfq')
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
        # Standard de purchase.purchase_rfq injeta `search_default_rfq` e
        # similares que filtram so rascunhos. Removidos para que a lista
        # mostre POs em qualquer estado.
        keys_to_remove = [key for key in sanitized_context if key.startswith('search_default_')]
        for key in keys_to_remove:
            sanitized_context.pop(key, None)
        action['context'] = sanitized_context
        return action
