# -*- coding: utf-8 -*-

import math
from odoo import http, _
from odoo.tools import lazy
from odoo.fields import Domain
from collections import Counter
from collections import defaultdict
from odoo.http import request, route
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import WebsiteSale, TableCompute

class WebsiteSaleAlanShop(WebsiteSale):

    @route('/get_offcanvas_category', auth='public', type='jsonrpc', website=True)
    def get_offcanvas_category(self, parent_id=None, **kw):
        """Return hierarchical categories with product count."""
        Category = request.env['product.public.category'].sudo()
        Product = request.env['product.template'].sudo()
        website = request.env['website'].get_current_website()
        website_domain = website.website_domain()
        if parent_id:
            categs_domain = Domain('parent_id', '=', int(parent_id)) & website_domain
        else:
            categs_domain = Domain('parent_id', '=', False) & website_domain

        if not self.env.user._is_internal():
            categs_domain &= Domain('has_published_products', '=', True)
        categories = Category.search_fetch(categs_domain)
        # ---------------- Get category product counts using the method ----------------
        category_count = self._count_category_products()
        categories_data = []
        current_parent = None

        # ------------ Get current parent info if navigating into subcategories ------------
        if parent_id:
            current_parent = Category.browse(int(parent_id))
            if current_parent.exists():
                current_parent = {
                    'id': current_parent.id,
                    'name': current_parent.name,
                    'parent_id': current_parent.parent_id.id if current_parent.parent_id else False,
                }

        for cat in categories:
            category_id = cat['id']
            has_children = Category.search_count([('parent_id', '=', category_id)], limit=1) > 0
            categories_data.append({
                'id': category_id,
                'name': cat['name'],
                'product_count': category_count.get(category_id, 0),
                'has_children': has_children,
                'parent_id': cat['parent_id'][0] if cat['parent_id'] else False,
                'image_url': f"/web/image/product.public.category/{category_id}/image_128",
            })

        return request.env['ir.ui.view']._render_template('theme_alan.as_offcanvas_categories_content',{
            'categories': categories_data,
            'current_parent': current_parent,
        })

    @route('/get_similar_product', auth='public', type='jsonrpc', website=True, cors='*')
    def similar_product(self, **kw):
        """Return similar/alternative products for a given product."""
        product_id = kw.get('product_id')
        domain = Domain.AND([request.website.sale_product_domain(), [('id', '=', product_id)]])
        product = request.env['product.template'].sudo().search(domain, limit=1)
        if not product.exists():
            return False
        return request.env['ir.ui.view']._render_template(
            'theme_alan.as_similar_product',
            {'products': product.alternative_product_ids}
        )

    def hide_out_of_stock(self, product):
        website = request.env['website'].get_current_website()
        total_free_qty = sum(website._get_product_available_qty(prod) for prod in product.sudo().product_variant_ids)
        if not product.sudo().allow_out_of_stock_order and total_free_qty < 1:
            return False
        return product.id

    def _shop_lookup_products(self, options, post, search, website):
        product_count, details, fuzzy_search_term = website.sudo()._search_with_fuzzy('products_only', search,
                                                                               limit=None,
                                                                               order=self._get_search_order(post),
                                                                               options=options)
        search_result = details[0].get('results', request.env['product.template']).with_context(bin_size=True)
        only_stock = request.session.get('stock', False)
        if only_stock:
            search_result = search_result.filtered(lambda product: self.hide_out_of_stock(product))
        if request.env.user._is_public():
            search_result = search_result.filtered(lambda x: x.is_published and x.sale_ok)
        return fuzzy_search_term, product_count, search_result

    def _count_category_products(self):
        Category = request.env['product.public.category'].sudo()
        Product = request.env['product.template'].sudo()
        categories = Category.search([])
        product_domain = [
            ('public_categ_ids', 'in', categories.ids),('sale_ok', '=', True)
        ]
        if request.env.user._is_public():
            product_domain.append(('is_published', '=', True))

        products = Product.search(product_domain)

        child_map = {
            categ.id: set(Category.search([('id', 'child_of', categ.id)]).ids)
            for categ in categories
        }

        category_count = {}
        for categ in categories:
            child_ids = child_map[categ.id]
            category_count[categ.id] = len(
                products.filtered(
                    lambda p: any(c.id in child_ids for c in p.public_categ_ids)
                )
            )
        return category_count

    def _rbt_count(self, search_product, brand_list, tag_list, attributes):
        tag_count = { tag.id: len(tag.product_template_ids.sudo().filtered(lambda x: x in search_product)) for tag in tag_list}
        attr_count = { attr.id : len(attr.pav_attribute_line_ids.mapped('product_tmpl_id').sudo().filtered(lambda x: x in search_product)) for attr in attributes.mapped('value_ids')}
        brand_count = { brand.id : len(brand.brand_product_ids.sudo().filtered(lambda x: x in search_product)) for brand in brand_list}
        rating_count = Counter(rat for prod in search_product.sudo().filtered(lambda x: not all(rating.sudo().is_internal for rating in x.rating_ids))for rat in range(1, 6)if prod.sudo().product_rating >= rat)
        rating_count.update({rating: 0 for rating in range(1, 6) if rating not in rating_count})
        return tag_count, attr_count, brand_count, rating_count

    @http.route()
    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, tags='', **post):

        # --- Handle Stock Filter ---
        stock_status = post.get('stock')
        if stock_status in ('active', 'inactive'):
            request.session['stock'] = stock_status == 'active'
        only_stock = request.session.get('stock', False)

        # --- Brand and Rating Filters ---
        def parse_filter(param):
            values = request.httprequest.args.getlist(param)
            if len(values) == 1 and ',' in values[0]:
                return [int(v) for v in values[0].split(',') if v.isdigit()]
            return [int(v) for v in values if v.isdigit()]

        brand_set = parse_filter('brands')
        rating_set = parse_filter('ratings')

        # --- Update Context ---
        request.update_env(context=dict(request.env.context, brands=brand_set, ratings=rating_set))

        res = super().shop(page, category, search, min_price, max_price, tags, **post)

        website = request.env['website'].get_current_website()
        website_domain = website.website_domain()

        # --- Alan Load More  ---
        url = self._get_shop_path(category)
        as_search_prds = res.qcontext['search_product']

        as_ppg = res.qcontext['ppg']
        ofst = 0
        alan_pager = request.website.pager(
            url=url,
            total=res.qcontext['search_count'],
            page=page,
            step=as_ppg,
            scope=res.qcontext['search_count'],
            url_args=post
        )

        total = res.qcontext['search_count']
        page_count = math.ceil(total / as_ppg)
        alan_pager['pages'] = [
            {'num': i, 'url': '/shop' if i == 1 else f'{url}/page/{i}', 'is_current': (i == page)}
            for i in range(1, page_count + 1)
        ]

        # --- Attach product IDs ---
        for page_data in alan_pager['pages']:
            page_data.update(prd_ids=as_search_prds[ofst:ofst + as_ppg].ids)
            ofst += as_ppg

        res.qcontext.update({'alan_pager': alan_pager})

        # --- Brand Filter Data ---
        brand_ids = request.env['as.product.brand'].search(
            Domain.AND([[('brand_product_ids.is_published', '=', True)], website_domain])
        )

        # --- Rating Filter Data ---
        as_search_prds = res.qcontext['search_product']
        rating_max = int(max(as_search_prds.mapped('rating_avg'), default=0)) + 1

        # --- Attribute Filter Data ---
        attrib_set = res.qcontext.get('attrib_set', [])
        filter_values = request.env['product.attribute.value'].browse(attrib_set).exists()
        filter_attributes = request.env['product.attribute'].search([('value_ids', 'in', filter_values.ids)])

        # --- Counts ---
        tag_count, attr_count, brand_count, rating_count = self._rbt_count(
            as_search_prds, brand_ids, res.qcontext.get('all_tags', []), res.qcontext.get('attributes', [])
        )
        category_count = self._count_category_products()
        is_shop_rmp_active = request.env['ir.config_parameter'].sudo().get_param('atharva_theme_base.allow_shop_page')

        # --- Update Template Context ---
        res.qcontext.update({
            'as_shop': True,
            'all_brands': brand_ids,
            'brands': brand_set,
            'all_ratings': rating_max,
            'ratings': rating_set,
            'filter_attributes': filter_attributes,
            'filter_values': filter_values,
            'selected_brands': request.env['as.product.brand'].browse(brand_set),
            'selected_tags': request.env['product.tag'].browse(res.qcontext.get('tags')),
            'category_count': category_count,
            'tag_count': tag_count,
            'rating_count': rating_count,
            'attr_count': attr_count,
            'brand_count': brand_count,
            'total_product': len(res.qcontext.get('search_product')),
            'is_shop_rmp_active':bool(is_shop_rmp_active),
            'stock_only': only_stock,
        })

        return res

    @http.route('/nextpage/products', auth='public', type='jsonrpc', website=True, csrf=False)
    def nextpage_products(self, **kw):
        if kw.get('product_ids'):
            products = request.env['product.template'].sudo()
            if kw.get('products'):
                products = request.env['product.template'].sudo().browse(kw.get('products'))
            website = request.env['website'].get_current_website()
            ppg = int(request.session.get('ppg') or 20)
            ppr = int(kw.get('ppr') or 4)
            product_ids = request.env['product.template'].sudo().browse(kw.get('product_ids'))
            products |= product_ids
            products_prices = lazy(lambda: product_ids._get_sales_prices(website))
            product_ids_objs = product_ids
            if request.env.user._is_public():
                product_ids_objs = product_ids_objs.filtered(lambda x: x.is_published and x.sale_ok)
            product_variants = {
                product: product.product_variant_ids[:1]
                for product in product_ids_objs
            }
            keep = QueryURL('/shop',)
            return request.env['ir.ui.view']._render_template('theme_alan.shop_page_next_products',{
                'bins': lazy(lambda: TableCompute().process(product_ids.sudo(), max(ppg, len(product_ids)), ppr)),
                'ppg':ppg,
                'ppr':ppr,
                'keep': keep,
                'products': products,
                'products_prices': products_prices,
                'product_variants': product_variants,
                'get_product_prices': lambda product: lazy(lambda: products_prices[product.id]),
                'products_in_wishlist': request.env['product.wishlist'].sudo().current().product_id.product_tmpl_id,
                'previewed_attribute_values': products._get_previewed_attribute_values(),
            })
        return {}

class AlanShopConfig(http.Controller):

    @http.route(['/get_alan_configuration'], type='jsonrpc', auth='user')
    def get_alan_configuration(self, **kwargs):
        """Get or set website configuration dynamically from builder."""
        website = request.env['website'].get_current_website()

        if not request.env.user.has_group('website.group_website_designer'):
            return {'error': 'unauthorized'}

        if kwargs:
            for field, value in kwargs.items():
                if hasattr(website, field):
                    website.sudo().write({field: bool(value)})
            return {field: getattr(website, field) for field in kwargs.keys()}

        data = {
            'active_b2b_signup': website.active_b2b_signup,
            'active_login_popup':website.active_login_popup,
            'active_user_dashboard_popup':website.active_user_dashboard_popup,
            'active_mini_cart':website.active_mini_cart,
            'active_b2b_mode':website.active_b2b_mode,
            'active_free_shipping':website.active_free_shipping,

            'active_shop_similar_product': website.active_shop_similar_product,
            'active_shop_quick_view': website.active_shop_quick_view,
            'active_brand_filter': website.active_brand_filter,
            'active_rating_filter': website.active_rating_filter,
            'active_stock_only': website.active_stock_only,
            'active_attribute_count': website.active_attribute_count,
            'active_shop_clear_filter': website.active_shop_clear_filter,
            'active_attribute_search': website.active_attribute_search,
            'active_hide_zero_attribute': website.active_hide_zero_attribute,
            'active_shop_offer_timer': website.active_shop_offer_timer ,
            'active_shop_brand_info': website.active_shop_brand_info,
            'active_load_more':website.active_load_more,
            'active_shop_product_reference':website.active_shop_product_reference,
            'active_shop_page_discount': website.active_shop_page_discount,
            'active_shop_stock_info': website.active_shop_stock_info,

            'active_product_offer_timer':website.active_product_offer_timer,
            'active_product_reference':website.active_product_reference,
            'active_product_category':website.active_product_category,
            'active_product_brand':website.active_product_brand,
            'active_product_advance_info':website.active_product_advance_info,
            'active_product_variant_info':website.active_product_variant_info,
            'active_product_accessory':website.active_product_accessory,
            'active_product_alternative':website.active_product_alternative,
            'active_product_pager':website.active_product_pager,
            'active_product_sticky':website.active_product_sticky,
            'active_product_bulk_save':website.active_product_bulk_save,
            'active_last_month_count': website.active_last_month_count,
            'active_product_inquiry': website.active_product_inquiry,
            'active_product_discount': website.active_product_discount,
            'active_product_visitor':website.active_product_visitor,
            'active_shop_product_barcode':website.active_shop_product_barcode,
            'active_delivery_check':website.active_delivery_check,
        }

        return data
