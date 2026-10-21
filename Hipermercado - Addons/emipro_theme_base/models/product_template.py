# -*- coding: utf-8 -*-
""" Inherit the product template model"""

from odoo.fields import Domain
from odoo import models, fields
from odoo.http import request

_MODEL_PRODUCT_TAB_LINE = 'product.tab.line'


class ProductTemplate(models.Model):
    """ Inherit the product template model to add product tabs and brand fields """

    _inherit = "product.template"

    tab_line_ids = fields.One2many(_MODEL_PRODUCT_TAB_LINE, 'product_id', 'Product Tabs',
                                   compute="_get_product_tabs",
                                   inverse="_set_product_tabs", help="Set the product tabs")
    product_brand_id = fields.Many2one('product.brand', string='Brand', help='Brand for this product')
    min_order_qty = fields.Integer(string='Minimum Order Quantity', default=1.0)

    def write(self, vals):
        tab_lines = vals.get('tab_line_ids')
        if tab_lines:
            tab_line_obj = self.env[_MODEL_PRODUCT_TAB_LINE]
            for value in tab_lines:
                operation, tab_id_or_str, tab_data = value

                if isinstance(tab_id_or_str, int):
                    tab_line = tab_line_obj.browse(tab_id_or_str)

                    if operation == 1 and tab_line.tab_type == 'global':
                        websites_ids = tab_line.website_ids.ids or []
                        vals_tab = {
                            'is_modified': True,
                            'parent_id': tab_line.id,
                            'product_id': self.id,
                            'tab_type': 'specific product',
                            'tab_content': tab_data.get('tab_content') or tab_line.tab_content,
                            'sequence': tab_line.sequence,
                            'website_ids': [[6, 0, websites_ids]],
                        }
                        tab_line_obj.create(vals_tab)

                    elif operation == 2 and tab_line.tab_type != 'global':
                        tab_line.unlink()

                elif isinstance(tab_id_or_str, str) and operation == 0:
                    tab_data.update({'product_id': self.id})
                    tab_line_obj.create(tab_data)

        return super(ProductTemplate, self).write(vals)

    def _get_product_tabs(self):
        for product in self:
            all_global_product_tabs = self.env[_MODEL_PRODUCT_TAB_LINE].search(
                [('tab_type', '=', 'global')])
            product_tabs = self.env[_MODEL_PRODUCT_TAB_LINE].search([('product_id', '=', self.id)])
            all_products_tabs = all_global_product_tabs + product_tabs
            product_tabs = all_products_tabs.ids
            for product_tab in all_products_tabs:
                if product_tab.is_modified == True and product_tab.product_id.id == self.id and product_tab.parent_id:
                    if product_tab.parent_id.id in product_tabs:
                        product_tabs.remove(product_tab.parent_id.id)

            product.tab_line_ids = [(6, 0, product_tabs)]

    def _set_product_tabs(self):
        return True

    def check_stock_availability_message(self):
        stock = 0
        for product in self.product_variant_ids:
            stock += product.sudo().with_context(warehouse=request.website.warehouse_id.id).free_qty
        return int(stock) if self.show_availability and int(stock) < self.available_threshold else False

    def _search_get_detail(self, website, order, options):
        # Brand Filter
        # brand_ids = None
        # if 'attribute_value_dict' in options and 0 in options['attribute_value_dict']:
        #     brand_ids = options.get('attribute_value_dict').get(0)
        #     options['attribute_value_dict'].pop(0)
        # brand_ids = options.get('attribute_value_dict', {}).pop(0, None)

        res = super()._search_get_detail(website, order, options)

        base_domain = []

        def add_domain(extra):
            """ Add extra domain to base_domain """

            nonlocal base_domain
            base_domain = Domain.AND([base_domain, extra])

        # Brand Filter via request_args
        request_args = options.get('request_args', [])
        brand_ids = [int(v.split("-")[1]) for v in request_args if v and v.startswith("0-")]
        if brand_ids:
            add_domain([('product_brand_id', 'in', brand_ids)])

        # OUT OF STOCK
        if options.get('out_of_stock'):
            add_domain(
                Domain.OR([[('product_variant_ids.free_qty', '>', 0)], [('allow_out_of_stock_order', '=', True)]]))

        # Brand Page
        if options.get('brand_val'):
            add_domain([('product_brand_id', 'in', options.get('brand_val').id)])

        # Rating Filter
        if options.get('ratings', False):
            add_domain([('rating_ids.rating', 'in', options.get('ratings'))])

        # Range Filter
        attrib_range_params = request.httprequest.args.getlist('attrib_range')
        attrib_range_values = []

        def parse_value(val):
            """ Parse the value to int or float if possible """

            try:
                float_val = float(val)
                if '.' in val or 'e' in val.lower():
                    return float_val
                else:
                    return int(float_val)
            except Exception:
                return val

        for param in attrib_range_params:
            try:
                attr_id, min_val, max_val = param.split(',')
                min_val = parse_value(min_val)
                max_val = parse_value(max_val)
                attrib_range_values.append((int(attr_id), min_val, max_val))
            except Exception:
                continue

        matching_value_ids = set()

        for attr_id, min_val, max_val in attrib_range_values:
            value_recs = request.env['product.attribute.value'].search([('attribute_id', '=', attr_id),
                                                                        ('name', '>=', min_val),
                                                                        ('name', '<=', max_val)])
            matching_value_ids |= set(value_recs.ids)
            add_domain([('attribute_line_ids.value_ids', 'in', list(matching_value_ids))])

        res['base_domain'].append(base_domain)

        return res

    def out_of_stock(self):
        stock = 0
        for product in self.product_variant_ids:
            stock += product.sudo().with_context(warehouse=request.website.warehouse_id.id).free_qty
        if self.type == 'consu' and self.is_storable == True and not self.allow_out_of_stock_order and stock < 1:
            return True
        return False

    def remove_cart_button(self):
        return self.sudo().out_of_stock()

    def get_previous_product(self):
        previous_product_tmpl = self.sudo().search([('website_sequence', '<', self.website_sequence),
                                                    ('website_published', '=', self.website_published), ],
                                                   order='website_sequence DESC', limit=1)
        return previous_product_tmpl or False

    def get_next_prodcut(self):
        next_prodcut_tmpl = self.sudo().search([('website_sequence', '>', self.website_sequence),
                                                ('website_published', '=', self.website_published), ],
                                               order='website_sequence ASC', limit=1)

        return next_prodcut_tmpl or False
