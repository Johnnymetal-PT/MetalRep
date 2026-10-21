# -*- coding: utf-8 -*-
"""Imports HTTP and website controllers."""

import logging
import datetime
import json
import ast

from odoo import http, fields, _
from odoo.http import request, route
from odoo.tools import consteq, lazy, str2bool
from odoo.fields import Domain
from werkzeug.exceptions import NotFound
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale_wishlist.controllers.main import WebsiteSaleWishlist
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.website_sale.controllers.variant import WebsiteSaleVariantController
from odoo.addons.website.controllers.main import Website
from odoo.addons.website_sale.controllers.cart import Cart as WebsiteSaleCart
from werkzeug.datastructures import ImmutableMultiDict

_logger = logging.getLogger(__name__)

# Constants for the module
_MODEL_PRODUCT_TEMPLATE = 'product.template'
_MODEL_PRODUCT_PRODUCT = 'product.product'
_MODEL_PRODUCT_BRAND = 'product.brand'
_MODEL_PRODUCT_TEMPLATE_ATTRIBUTE_VALUE = 'product.template.attribute.value'
_MODEL_WISHLIST_COLLECTION = 'wishlist.collection'
_MODEL_PRODUCT_LINE = 'product.line'
_MODEL_PRODUCT_WISHLIST = 'product.wishlist'


class CustomerPortalExt(CustomerPortal):
    """
    Extension of Odoo's Customer Portal Class.
    """

    def _prepare_address_form_values(self, *args, address_type='billing',
                                     use_delivery_as_billing=False, **kwargs):
        """
        Purpose for setting default country and allowed countries in address form.
        This method overrides the original method in CustomerPortal to customize
        the address form values based on the current website's settings.
        Added by: Shubham Kumar
        Date: 6 Oct 2025
        :param args: tuple
        :param address_type: default -> 'billing'
        :param use_delivery_as_billing: default -> False
        :param kwargs: **kwargs
        :return: rendering_values -> dict
        """
        rendering_values = super()._prepare_address_form_values(*args, address_type=address_type,
                                                                use_delivery_as_billing=use_delivery_as_billing,
                                                                **kwargs)
        countries = rendering_values.get('countries', False)
        partner_id = rendering_values.get('partner_sudo', False)
        current_website = request.env['website'].get_current_website()

        if countries:
            allow_countries = set(current_website.allow_countries or countries)

            if partner_id and partner_id.country_id:
                allow_countries.add(partner_id.country_id)

            allowed_countries = allow_countries or countries

            rendering_values.update({
                'countries': allowed_countries,
                'default_country_id': current_website.default_country_id
                if current_website.default_country_id else None
            })

        return rendering_values


class EmiproThemeBase(http.Controller):
    """
    Emipro Theme Base's Custom Class.
    """

    @http.route(['/get_categories_list_data'], type='jsonrpc', auth="public", website=True)
    def categories_list_data(self):
        """
        Returns a rendered HTML template containing top-level product categories and their product counts.
        Used to populate the mobile category list dynamically when a user interacts with the header icon.
        """
        current_website = request.website.get_current_website()
        all_categories = request.env['product.public.category'].sudo().search(
            [('website_id', 'in', (False, current_website.id)), ('parent_id', '=', False)])
        category_data = [
            {
                'current_category': category,
                'product_count': request.env[_MODEL_PRODUCT_TEMPLATE].sudo().search_count(
                    [('public_categ_ids', 'child_of', category.id)]),
            }
            for category in all_categories
        ]
        if category_data:
            values = {
                'categories': category_data,
            }
            return http.Response(template="emipro_theme_base.mobile_header_categories_option_view_container",
                                 qcontext=values).render()
        else:
            return None

    @route(route='/shop/clear_cart', type='jsonrpc', auth='public', website=True)
    def clear_cart(self):
        request.cart.order_line.unlink()
        request.session['website_sale_cart_quantity'] = 0

    @http.route('/see_all', type='jsonrpc', auth="public", methods=['POST'], website=True)
    def get_see_all(self, attr_type=None, attr_id=None, attrib_set=None, counts=None):
        attribute_obj = request.env['product.attribute'].browse(int(attr_id))
        counts = counts and ast.literal_eval(counts)

        if attr_type == 'color':
            response = http.Response(template="website_sale.filter_color_attributes",
                                     qcontext={'a': attribute_obj, 'attrib_set': attrib_set or set(),
                                               'counts': counts or {}})
        elif attr_type == 'image':
            response = http.Response(template="website_sale.filter_image_attributes",
                                     qcontext={'a': attribute_obj, 'attrib_set': attrib_set or set(),
                                               'counts': counts or {}})

        elif attr_type == 'pills':
            response = http.Response(template="website_sale.filter_pills_attributes",
                                     qcontext={'a': attribute_obj, 'attrib_set': attrib_set or set(),
                                               'counts': counts or {}})
        return response.render()

    @http.route(['/similar_products_item_data'], type='http', auth="public", website=True)
    def similar_products_item_data(self, product_id=None):
        if not product_id:
            return

        product = request.env[_MODEL_PRODUCT_TEMPLATE].browse(int(product_id))
        website_ids = [False, request.website.id]
        alternative_products = product.alternative_product_ids.filtered(
            lambda p: p.sale_ok and p.website_id.id in website_ids)
        alternative_products_details = [p._get_combination_info() for p in alternative_products]
        values = {'alternative_products': alternative_products_details, 'website': request.website}
        return http.Response(template="emipro_theme_base.similar_products_view_container", qcontext=values).render()

    @http.route(['/rename_collection'], type='jsonrpc', auth='public', website=True)
    def rename_collection(self, collection_name=None, collection_id=None):
        res = False
        if collection_id and collection_name:
            collection = request.env[_MODEL_WISHLIST_COLLECTION].sudo().browse(int(collection_id))
            collection.name = collection_name
            res = True
        return res

    @http.route('/select_collection_modal_data', auth='public', type='jsonrpc', website=True)
    def select_collection_modal_data(self):
        """ Render collection popup for logged-in user
        """
        return http.Response(template="theme_clarico_vega.select_collection_popup_tmpl",
                             qcontext={}).render()

    @http.route(['/check_collection'], type='jsonrpc', auth='user', website=True)
    def _check_collection(self, collection_id=None):
        """ This controller will check either products are available in collection or not
            return: True if contains at least one product else False
        """
        res = False
        if collection_id:
            collection = request.env[_MODEL_WISHLIST_COLLECTION].sudo().browse(int(collection_id))
            res = True if collection.product_line_ids else False
        return res

    @http.route('/check_collections', auth='public', type='jsonrpc', website=True)
    def _check_collections(self):
        """ Check collections are available or not for current logged-in user.
        :return: dict
        """
        res = {}
        user = request.env.user.sudo()
        res['is_partner'] = False if user.id == request.env.ref(
            'base.public_user').id else user.partner_id
        collections = request.env[_MODEL_WISHLIST_COLLECTION].get_partner_collections(user.partner_id)
        res['collections'] = collections or False
        return res

    @http.route('/check_collection_name', auth='user', type='jsonrpc', website=True)
    def check_collection_name(self, collection_name):
        """ Check collection name is valid or not
        :param collection_name: Name of collection entered by User
        :return: True if collection name is valid else False
        """
        res = True
        partner = request.env.user.sudo().partner_id
        collections = request.env[_MODEL_WISHLIST_COLLECTION].get_partner_collections(partner)
        if collection_name in collections.mapped('name') or \
                collection_name.isspace() or not len(collection_name):
            res = False
        return res

    @http.route('/add_select_collection', auth='user', type='jsonrpc', website=True)
    def add_select_collection(self, collection_name):
        """ Create new collection.
        :param collection_name: name of collection
        :return: string id of created collection
        """
        partner = request.env.user.sudo().partner_id
        collection = request.env[_MODEL_WISHLIST_COLLECTION].sudo()
        collections = collection.get_partner_collections(partner)
        if len(collection_name) and collection_name not in collections.mapped('name'):
            vals = {'name': collection_name, 'partner_id': partner.id}
            collection = collection.create(vals)
        return str(collection.id)

    @http.route('/add_product_in_collection', auth='user', type='jsonrpc', website=True)
    def add_product_in_collection(self, collection_id, product_id, product_qty):
        """ Add product in selected collection.
        :param collection_id: id of selected collection
        :param product_id: id of the product that will be added in collection
        :param product_qty: quantity of product
        :return: bool
        """
        res = False
        collection = request.env[_MODEL_WISHLIST_COLLECTION].sudo().browse(int(collection_id))
        product = request.env[_MODEL_PRODUCT_PRODUCT].sudo().browse(int(product_id))
        line_product_ids = collection.product_line_ids.mapped('product_id') or False

        if product:
            if line_product_ids and product.id in line_product_ids.ids:
                res = False
            else:
                vals = {'collection_id': collection.id, 'product_id': product.id, 'quantity': int(product_qty)}
                request.env[_MODEL_PRODUCT_LINE].sudo().create(vals)
                res = True

        return res

    @http.route('/check_product_in_collection', auth='user', type='jsonrpc', website=True)
    def check_product_in_collection(self, collection_id, product_id):
        """ Check whether product is already exist in collection or not
        :param collection_id: id of collection in string
        :param product_id: id of product in string
        :return: True if product already exist in collection else False
        """
        res = False
        collection = request.env[_MODEL_WISHLIST_COLLECTION].sudo().browse(int(collection_id))
        line_product_ids = collection.product_line_ids.mapped('product_id') or False
        if line_product_ids and product_id in line_product_ids.ids:
            res = True
        return res

    @http.route('/add_to_cart_collection', type='jsonrpc', auth='user', website=True)
    def add_to_cart_collection(self, product_line_id=None):
        """ Update products to cart when a user clicks Add to Cart button,
        also redirect user to cart"""
        product_line = request.env[_MODEL_PRODUCT_LINE].sudo().browse(
            int(product_line_id)) if product_line_id else None
        current_cart_order = request.website._create_cart()
        res = False
        if product_line:
            res = current_cart_order._cart_add(product_id=product_line.product_id.id,
                                               quantity=product_line.quantity)
        return res

    @http.route('/remove_collection', auth='user', type='jsonrpc', website=True)
    def remove_collection(self, collection_id):
        """ Remove collection if logged-in user and partner of collection are same.
        :param collection_id: id of collection in string
        :return: True if collection removed else False
        """
        partner = request.env.user.sudo().partner_id
        collection = request.env[_MODEL_WISHLIST_COLLECTION].sudo().browse(int(collection_id))
        res = False
        if collection.partner_id == partner:
            wishes = request.env[_MODEL_PRODUCT_WISHLIST].sudo().search(
                [('partner_id', '=', partner.id),
                 ('product_id', 'in', collection.product_line_ids.product_id.ids)]
            ) if partner and collection.product_line_ids else request.env[_MODEL_PRODUCT_WISHLIST].sudo()
            if wishes:
                # Remove wishes which is associated with current partner and products of the current collection.
                wishes.sudo().unlink()
            collection.product_line_ids.unlink()
            res = collection.unlink()
        return res

    @http.route('/remove_product', auth='user', type='jsonrpc', website=True)
    def remove_product(self, product_line_id):
        """ Remove product from collection(list) and also remove wishlist record where product is linked.
        :param product_line_id: product line of list
        :return: collection
        """
        product_line_id = request.env[_MODEL_PRODUCT_LINE].sudo().browse(int(product_line_id))

        partner = request.env.user.sudo().partner_id
        wish = request.env[_MODEL_PRODUCT_WISHLIST].sudo().search(
            [('partner_id', '=', partner.id), ('product_id', '=', product_line_id.product_id.id)]
        ) if partner and product_line_id else request.env[_MODEL_PRODUCT_WISHLIST].sudo()
        if wish:
            # Remove wish which is associated with current partner and product.
            wish.sudo().unlink()

        collection = product_line_id.collection_id
        product_line_id.unlink()
        return collection

    @http.route('/shop/wishlist/all_products', auth='public', type='jsonrpc', website=True)
    def shop_wishlist_all_products(self):
        values = request.env[_MODEL_PRODUCT_WISHLIST].with_context(display_default_code=False).current()
        return json.dumps(values.mapped('product_id').ids)

    @http.route('/send_collection', auth='user', type='jsonrpc', website=True)
    def send_collection(self, collection_id=None, recipient_email=None):
        res = False

        collection = request.env[_MODEL_WISHLIST_COLLECTION].sudo().browse(int(collection_id))

        template = request.env.ref('emipro_theme_base.share_wishlist_collection_email', raise_if_not_found=False)

        if template:
            try:
                email_values = {'email_to': recipient_email,
                                'subject': "%s has shared a wishlist with you!" % collection.partner_id.name,
                                'email_from': request.env.company.email_formatted}
                template.send_mail(collection.id, email_values=email_values)
                _logger.info("<%s> Shared wishlist to <%s>", collection.partner_id.name, recipient_email)
                res = True
            except Exception as e:
                _logger.info("Error occured while sharing wishlist %s", str(e))

        return res

    @http.route('/get_product_info', auth='public', type='jsonrpc', website=True)
    def get_product_info(self, product_id=None):
        if product_id:
            product = request.env[_MODEL_PRODUCT_TEMPLATE].browse(int(product_id))
            return http.Response(template="theme_clarico_vega.product_pager",
                                 qcontext={'product': product}).render()
        else:
            return None

    # Render the Hotspot Product popover template
    @http.route('/get-pop-up-product-details', type='http', auth='public', website=True)
    def get_popup_product_details(self, **kw):
        """
        Render the Hotspot Product popover template
        @param kw: dict for product details
        @return: response for template
        """
        product = int(kw.get('product')) if kw.get('product') else False
        if product:
            product = request.env[_MODEL_PRODUCT_TEMPLATE].sudo().browse(product)
            values = {'product': product}
            return request.render("theme_clarico_vega.product_add_to_cart_popover", values,
                                  headers={'Cache-Control': 'no-cache'})

    @http.route(['/quick_view_item_data'], type='jsonrpc', auth="public", website=True)
    def get_quick_view_item(self, product_id=None):
        if product_id:
            product = request.env[_MODEL_PRODUCT_TEMPLATE].browse(int(product_id))
            return http.Response(template="emipro_theme_base.quick_view_container",
                                 qcontext={'product': product}).render()
        return None

    @http.route('/shop/cart/get_total', type='jsonrpc', auth='public', website=True)
    def get_cart_total(self, order_id=None):
        """ Used get_cart_total method to include cart summary details. .
            :return: dict
        """
        session_order_id = request.session.get('sale_order_id') or order_id
        order = request.env['sale.order'].sudo().browse(session_order_id) if session_order_id else False
        currency = order and order.currency_id
        if not order:
            return {
                'cart_total': 0.0,
                'cart_currency': request.website.currency_id.symbol,
                'cart_currency_code': request.website.currency_id.name,
                'cart_currency_position': request.website.currency_id.position,
            }
        return {
            'cart_total': float(order.amount_total),
            'cart_currency': currency.symbol,
            'cart_currency_code': currency.name,
            'cart_currency_position': currency.position,
        }

    @route('/age_verification/init', type='jsonrpc', auth="public", website=True)
    def get_age_verification_config(self, **kwargs):
        website = request.website
        is_enable_age_verification = website.enable_age_verification
        data_dict = {'is_enable_age_verification': is_enable_age_verification}
        if is_enable_age_verification:
            data_dict.update({'title': 'Age Verification',
                              'message': website.age_verification_message,
                              'warning': website.age_verification_warning,
                              'background_image': website.background_image_age_verification,
                              'background_color': website.background_color_age_verification,
                              'yes_button_color': website.yes_button_color,
                              'yes_button_text_color': website.yes_button_text_color,
                              'no_button_color': website.no_button_color,
                              'no_button_text_color': website.no_button_text_color, })
        return data_dict

    @route('/age_verification/confirm', type='jsonrpc', auth="public", website=True)
    def confirm_age_verification(self, verified=False, **kwargs):
        if verified:
            request.session['age_verified'] = True
        return {'success': True, 'verified': verified}


class WebsiteSaleVariantControllerExt(WebsiteSaleVariantController):
    """
    Extension of Odoo's Website Sale Variant Controller Class.
    """

    @route()
    def get_combination_info_website(self, product_template_id, product_id, combination, add_qty,
                                     uom_id=None, **kwargs):
        res = super().get_combination_info_website(product_template_id=product_template_id,
                                                   product_id=product_id,
                                                   combination=combination,
                                                   add_qty=add_qty,
                                                   uom_id=uom_id, **kwargs)

        product_id = res.get('product_id', product_id)
        product = request.env[_MODEL_PRODUCT_PRODUCT].sudo().browse(int(product_id))
        product_template = (request.env[_MODEL_PRODUCT_TEMPLATE]
                            .sudo().browse(int(product_template_id)))
        pricelist = request.website._get_and_cache_current_pricelist()

        res.update({
            'sku_details': product.default_code if product_template.product_variant_count > 1 else
            product_template.default_code})
        # Price Table
        if product and product_template:
            if request.website.display_product_price():
                res['price_table_details'] = (pricelist.enable_price_table
                                              and self.get_price_table(pricelist,
                                                                       product, product_template))
        details = self.get_offer_details(pricelist, product, add_qty)
        res.update(details)

        return res

    def get_price_table(self, pricelist, product, product_tempate):
        current_date = datetime.datetime.now()
        pricelist_items = pricelist._get_applicable_rules(product, current_date)

        price_list_items = []
        minimum_qtys = set()
        minimum_qtys.add(1)
        for rule in pricelist_items:
            minimum_qtys.add(rule.min_quantity)
        minimum_qtys.discard(0)
        minimum_qtys = list(minimum_qtys)
        minimum_qtys.sort()
        show_qty = 1 in minimum_qtys and len(minimum_qtys) > 1

        for qty in minimum_qtys:
            price = pricelist._get_product_price(product=product,
                                                 quantity=qty,
                                                 target_currency=pricelist.currency_id)
            list_price = product.list_price or 0
            discount = 0
            if list_price and price:
                difference = round(list_price - price, 2)
                discount = round((difference * 100) / list_price, 2)
            data = {'qty': int(qty), 'price': price, 'disc_per': discount}
            price_list_items.append(data)

        price_list_vals = {
            'pricelist_items': price_list_items,
            'currency_id': pricelist.currency_id,
            'show_qty': show_qty,
        }

        return http.Response(template="emipro_theme_base.product_price_table",
                             qcontext=price_list_vals).render()

    def get_offer_details(self, pricelist, product, add_qty):
        offer_details = {
            'is_offer': False
        }
        try:
            vals = pricelist._compute_price_rule(product, add_qty)
            if vals.get(int(product)) and vals.get(int(product))[1]:
                suitable_rule = vals.get(int(product))[1]
                suitable_rule = request.env['product.pricelist.item'].sudo().browse(suitable_rule)
                if suitable_rule.date_end and suitable_rule.is_display_timer:
                    start_date = int(round(datetime.datetime.timestamp(suitable_rule.date_start) * 1000))
                    end_date = int(round(datetime.datetime.timestamp(suitable_rule.date_end) * 1000))
                    current_date = int(round(datetime.datetime.timestamp(datetime.datetime.now()) * 1000))
                    offer_details.update({
                        'is_offer': True,
                        'start_date': start_date,
                        'end_date': end_date,
                        'current_date': current_date,
                        'suitable_rule': suitable_rule,
                        'offer_msg': suitable_rule.offer_msg,
                    })
        except Exception:
            return offer_details
        return offer_details


class WebsiteExt(Website):
    """
    Extension of Odoo's Website Class.
    """

    @http.route()
    def autocomplete(self, search_type=None, term=None, order=None, limit=5, max_nb_chars=999, options=None):

        if search_type is None:
            search_type = 'products_only'

        res = super().autocomplete(search_type, term, order, limit, max_nb_chars, options)

        filtered_results = [rs for rs in res['results'] if rs.get('_fa') != 'fa-folder-o']
        res['results'] = filtered_results

        current_website = request.website.get_current_website()
        categories = request.env['product.public.category'].sudo().search(
            [('website_id', 'in', (False, current_website.id))]).filtered(
            lambda catg: term.strip().lower() in catg.name.strip().lower())

        search_categories = []
        for categ in categories:
            search_categories.append({'_fa': 'fa-folder-o', 'name': categ.name,
                                      'website_url': f'/shop/category/{categ.id}'})
        res['categories'] = search_categories[:5]

        selected_categories = []
        if current_website.enable_search_categ:
            for cat in current_website.search_categ_id[:5]:
                selected_categories.append({
                    "name": cat.name,
                    "website_url": f'/shop/category/{cat.id}',
                })

        res["selected_categories"] = selected_categories

        if term and current_website and current_website.enable_smart_search:
            is_quick_link = {'status': False}

            brands = request.env[_MODEL_PRODUCT_BRAND].sudo().search(
                [('website_id', 'in', (False, current_website.id)), ('website_published', '=', True)]).filtered(
                lambda b: term.strip().lower() in b.name.strip().lower())
            if brands and current_website.search_in_brands:
                search_brands = []
                for brand in brands:
                    search_brands.append({'_fa': 'fa-folder-o', 'name': brand.name,
                                          'website_url': f'/shop/brands/{brand.id}'})
                res['search_brands'] = search_brands[:5]

            if current_website.search_in_attributes_and_values:
                attribute_value = request.env['product.attribute.value'].sudo().search([]).filtered(
                    lambda value: term.strip().lower() == value.name.strip().lower())
                if not attribute_value:
                    attribute_value = request.env['product.attribute.value'].sudo().search([]).filtered(
                        lambda value: term.strip().lower() in value.name.strip().lower())

                if attribute_value:
                    is_quick_link.update({'status': True,
                                          'navigate_type': 'attr_value',
                                          'name': attribute_value[0].name,
                                          'attribute_name': attribute_value[0].attribute_id.name,
                                          'url': f'/shop?search=&attribute_value='
                                                 f'{attribute_value[0].attribute_id.id}-{attribute_value[0].id}'})
            res['is_quick_link'] = is_quick_link

        return res

    @http.route([
        '/website/search',
        '/website/search/page/<int:page>',
        '/website/search/<string:search_type>',
        '/website/search/<string:search_type>/page/<int:page>',
    ], type='http', auth="public", website=True, sitemap=False)
    def hybrid_list(self, page=1, search='', search_type='all', **kw):
        result = super().hybrid_list(page=page, search=search, search_type=search_type, **kw)

        curr_website = request.website.get_current_website()
        if search and curr_website.enable_smart_search:
            search_term = ' '.join(search.split()).strip().lower()
            if search_term:
                request.env['search.keyword.report'].sudo().create({
                    'search_term': search_term,
                    'no_of_products_in_result': result.qcontext.get('search_count', 0),
                    'user_id': request.env.user.id
                })

        return result

    @http.route(website=True, auth="public", sitemap=False, csrf=False)
    def web_login(self, *args, **kw):
        """
            Login - overwrite of the web login so that regular users are redirected to the backend
            while portal users are redirected to the same page from popup
            Returns formatted data required by login popup in a JSON compatible format
            Added by: Ashvin Rathod
            Date: 23 Oct 2025 {Modified on 10 Dec 2025}
        """
        login_form_ept = kw.get('login_form_ept', False)

        if 'login_form_ept' in kw.keys():
            kw.pop('login_form_ept')

        response = super().web_login(*args, **kw)

        if login_form_ept:
            error = response.qcontext.get('error')
            if response.is_qweb and error:
                return response

            if request.params.get('login_success'):
                credential = {'login': request.params['login'], 'password': request.params['password'],
                              'type': 'password'}
                uid = request.session.authenticate(request.env, credential)['uid']
                user = request.env['res.users'].browse(int(uid))

                if user.totp_enabled:
                    redirect = request.env(user=uid)['res.users'].browse(int(uid))._mfa_url()
                    return json.dumps({'redirect': redirect,
                                       'login_success': True,
                                       'hide_msg': True})

                redirect = (
                    '/web?' + request.httprequest.query_string.decode('utf-8')
                    if user.has_group('base.group_user')
                    else '/my'
                )

                return json.dumps({'redirect': redirect,
                                   'login_success': True,
                                   'hide_msg': False})
        return response

    @http.route(auth='public', website=True, sitemap=False, csrf=False)
    def web_auth_reset_password(self, *args, **kw):
        """
            Reset password from popup and redirect to the same page
            Returns formatted data required by login popup in a JSON compatible format
            Added by: Ashvin Rathod
            Date: 23 Oct 2025
        """
        reset_form_ept = kw.get('reset_form_ept', False)
        if 'reset_form_ept' in kw.keys():
            kw.pop('reset_form_ept')
        response = super().web_auth_reset_password(*args, **kw)
        if reset_form_ept:
            if response.is_qweb and response.qcontext.get('error', False):
                return json.dumps({'error': response.qcontext.get('error', False)})
            elif response.is_qweb and response.qcontext.get('message', False):
                return json.dumps({'message': response.qcontext.get('message', False)})
        return response


class WebsiteSaleExt(WebsiteSale):
    """
    Extension of Odoo's Website Sale Class.
    """

    @route([
        '/shop',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/<int:page>',
        '/shop/brands/<model("product.brand"):brand>',
        '/shop/brands/<model("product.brand"):brand>/page/<int:page>',
    ], type='http', auth="public", website=True, sitemap=WebsiteSale.sitemap_shop)
    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, tags='', **post):

        # For Brand Page
        brand_val = None
        if 'brand' in post:
            brand_val = post.get('brand')

        request_args = request.httprequest.args
        post.update(request_args=request_args.getlist('attribute_values', None))
        mutable_data = request_args.to_dict(flat=False)
        if 'attribute_values' in mutable_data:
            mutable_data['attribute_values'] = [value for value in mutable_data['attribute_values'] if
                                                value and not value.startswith('0')]
        request.httprequest.args = ImmutableMultiDict(mutable_data)

        res = super(WebsiteSaleExt, self).shop(page=page, category=category, search=search, min_price=min_price,
                                               max_price=max_price, tags=tags, **post)

        # Create Report for the search keyword
        curr_website = request.website.get_current_website()
        if search and curr_website.enable_smart_search:
            search_term = ' '.join(search.split()).strip().lower()
            attrib = res.qcontext.get('attrib_values', False)
            if search_term and not category and not attrib and page == 0:
                request.env['search.keyword.report'].sudo().create({
                    'search_term': search_term,
                    'no_of_products_in_result': res.qcontext.get('search_count', 0),
                    'user_id': request.env.user.id
                })

        res.qcontext.update({'brand_val': brand_val})

        return res

    def _shop_lookup_products(self, options, post, search, website):
        """
        Discount sorting functionality for products in the shop page.
        This method overrides the original method in WebsiteSale to add
        sorting based on discount percentage.
        Added by: Shubham Kumar
        Date: 8 Oct 2025
        :param options:
        :param post:
        :param search:
        :param website:
        :return:
        """
        discount = 'discount' in post.get('order', '')
        if discount:
            post.pop('order', None)

        top_sold = 'top_sold' in post.get('order', '')
        if top_sold:
            post.pop('order', None)

        fuzzy_search_term, product_count, search_result = super()._shop_lookup_products(options, post, search, website)

        def sort_function(product):
            """Calculate discount ratio for sorting."""

            list_price = product.get('list_price', 0)
            price = product.get('price', 0)
            # Calculate the discount ratio only if list_price is greater than price
            return (list_price - price) / list_price if list_price > price else 0

        if discount:
            # Get the product combination info and sort it directly in one step
            product_prices_data = sorted((product._get_combination_info() for product in search_result),
                                         key=sort_function, reverse=True)

            # Extract product template IDs and browse the sorted products
            product_template_ids = [p.get('product_template_id') for p in product_prices_data]
            search_result = request.env[_MODEL_PRODUCT_TEMPLATE].browse(product_template_ids)

        if top_sold:
            sales_data = {}
            top_sold_duration_days = request.website.top_sold_duration_days or 30
            cutoff_date = fields.Datetime.now() - datetime.timedelta(days=top_sold_duration_days)
            for product in search_result:
                total_sold = sum(request.env['sale.order.line'].sudo().search_count(
                    [('create_date', '>=', cutoff_date), ('product_id', '=', variant.id),
                     ('state', 'in', ['sale', 'done'])]) for variant in product.product_variant_ids)
                sales_data[product.id] = total_sold
            sorted_product_ids = sorted(sales_data, key=sales_data.get, reverse=True)
            search_result = request.env[_MODEL_PRODUCT_TEMPLATE].browse(sorted_product_ids)

        if 'out_of_stock' in options and options.get('out_of_stock'):
            warehouse = request.website.warehouse_id
            stock_location = warehouse.lot_stock_id

            """Return True if product has stock in current warehouse."""
            def is_in_stock(product_template):
                stock = 0
                for variant in product_template.product_variant_ids:
                    quants = request.env['stock.quant'].sudo().search([
                        ('product_id', '=', variant.id),
                        ('location_id', 'child_of', stock_location.id)
                    ])
                    stock += sum(quants.mapped('quantity'))

                # Apply your business rules
                if (product_template.type == 'consu'
                        and product_template.is_storable
                        and not product_template.allow_out_of_stock_order
                        and stock < 1):
                    return False
                return True

            # Keep only products that are in stock for this warehouse
            search_result = search_result.filtered(is_in_stock)
            product_count = len(search_result)

        return fuzzy_search_term, product_count, search_result

    def _get_attribute_value_counts(self, search_product):
        """Efficiently get counts of products per attribute value (Odoo 19 compatible)."""

        # Get all matching templates from the current filter/search context
        if not search_product:
            return {}

        # Use _read_group instead of deprecated read_group
        groups = request.env[_MODEL_PRODUCT_TEMPLATE_ATTRIBUTE_VALUE]._read_group(
            domain=[('product_tmpl_id', 'in', search_product.ids)],
            groupby=['product_attribute_value_id'],
            aggregates=['__count'])

        counts = {g[0].id: g[1] for g in groups if isinstance(g, tuple)}

        return counts

    @http.route('/search_sidebar_ept', type='http', auth='public', website=True, sitemap=False)
    def search_sidebar(self):
        return request.render('theme_clarico_vega.website_search_box_input_ept', headers={'Cache-Control': 'no-cache'})

    @route(['/shop/cart_popover'], type='http', auth="public", website=True, sitemap=False)
    def cart_popover(self, id=None, access_token=None, revive_method='', **post):
        """ Display the cart page.

        This route is responsible for the main cart management and abandoned cart revival logic.

        :param str id: The abandoned cart's id.
        :param str access_token: The abandoned cart's access token.
        :param str revive_method: The revival method for abandoned carts. Can be 'merge' or 'squash'.
        :return: The rendered cart page.
        :rtype: str
        """
        order_sudo = request.cart
        values = {}

        if id and access_token:
            abandoned_order = request.env['sale.order'].sudo().browse(int(id)).exists()
            if not abandoned_order or not consteq(abandoned_order.access_token, access_token):
                raise NotFound()
            if abandoned_order.state != 'draft':
                values.update({'abandoned_proceed': True})
            elif revive_method == 'squash' or (revive_method == 'merge' and not request.session.get('sale_order_id')):
                request.session['sale_order_id'] = abandoned_order.id
                return request.redirect('/shop/cart')
            elif revive_method == 'merge':
                abandoned_order.order_line.write({'order_id': request.session['sale_order_id']})
                abandoned_order.action_cancel()
            elif abandoned_order.id != request.session.get('sale_order_id'):
                values.update({'id': abandoned_order.id, 'access_token': abandoned_order.access_token})

        values.update({'website_sale_order': order_sudo,
                       'date': fields.Date.today(),
                       'suggested_products': []})

        if order_sudo:
            order_sudo.order_line.filtered(lambda sol: sol.product_id and not sol.product_id.active).unlink()
            values['suggested_products'] = order_sudo._cart_accessories()
            values.update(self._get_express_shop_payment_values(order_sudo))

        values.update(request.website._get_checkout_step_values())
        values.update(self._cart_values(**post))
        values.update(self._prepare_order_history())

        return request.render("emipro_theme_base.cart_popover", values)

    def _get_additional_shop_values(self, values, **kwargs):
        res = super()._get_additional_shop_values(values, **kwargs)

        search_product = values.get('search_product', None)
        base_domain = request.website.sale_product_domain()

        # Compute counts efficiently
        counts = self._get_attribute_value_counts(search_product)

        # Added brand records
        brands = lazy(lambda: request.env[_MODEL_PRODUCT_BRAND].search(
            [('product_ids', 'in', search_product and search_product.ids or []), ('website_published', '=', True)]))

        # Brand Product Count
        brand_count = {}

        for brand in brands:
            brand_domain = Domain.AND([base_domain, [('product_brand_id', '=', brand.id)]])
            brand_count[brand.id] = request.env[_MODEL_PRODUCT_TEMPLATE].search_count(brand_domain) or 0

        # Out of Stock Filter
        out_of_stock = False
        if 'out_of_stock' in kwargs:
            out_of_stock = True

        # Tag Product Count
        tag_count = {}

        for tag in values.get('all_tags', []):
            tag_domain = Domain.AND([base_domain, [('product_variant_ids.all_product_tag_ids', '=', tag.id)]])
            tag_count[tag.id] = request.env[_MODEL_PRODUCT_TEMPLATE].search_count(tag_domain) or 0

        # Range Filter
        request_args = request.httprequest.args
        attrib_range_values = request_args.getlist('attrib_range')
        attrib_range_value_pairs = [[float(v) for v in value.split(',')] for value in attrib_range_values if value]
        attrib_range_dict = {int(pair[0]): {'min': pair[1], 'max': pair[2]} for pair in attrib_range_value_pairs}

        range_attributes = 'attributes' in values and values.get('attributes').filtered(
            lambda l: l.display_type == 'range') or []
        range_attrs = {}
        for range_attribute in range_attributes:
            attr_values = range_attribute.value_ids
            min_value = float(min(attr_values.mapped('name')))
            max_value = float(max(attr_values.mapped('name')))
            range_attrs[range_attribute.id] = {'min': min_value, 'max': max_value}

        if kwargs.get('request_args', False):
            values.update({'request_args': kwargs.get('request_args')})

        values.update({'counts': counts, 'brands': brands, 'out_of_stock': out_of_stock, 'brand_count': brand_count,
                       'tag_count': tag_count, 'attrib_range_dict': attrib_range_dict, 'range_attrs': range_attrs})

        return res

    def _get_search_options(self, category=None, attribute_value_dict=None, tags=None, min_price=0.0, max_price=0.0,
                            conversion_rate=1, **post):

        res = super()._get_search_options(category=category, attribute_value_dict=attribute_value_dict, tags=tags,
                                          min_price=min_price, max_price=max_price, conversion_rate=conversion_rate,
                                          **post)

        out_of_stock = False
        if 'out_of_stock' in post or not request.website.display_out_of_stock:
            out_of_stock = True

        # For Brand Page
        brand_val = None
        if 'brand' in post:
            brand_val = post.get('brand')

        # For Rating Filter
        rating_list = request.httprequest.args.getlist('rating')
        if rating_list:
            rating_list = list(map(int, rating_list)) or []

        # For Range Filter
        attrib_range_list = []
        if 'attrib_range' in request.httprequest.args:
            attrib_range_list = request.httprequest.args.getlist('attrib_range')

        # For BRAND FILTER
        if post.get('request_args', False):
            res.update({'request_args': post.get('request_args')})

        res.update({'out_of_stock': out_of_stock, 'brand_val': brand_val, 'ratings': rating_list,
                    'attrib_range_list': attrib_range_list})

        return res

    def _prepare_product_values(self, product, category, **kwargs):
        res = super()._prepare_product_values(product, category, **kwargs)

        product_variant = res.get('product_variant')
        website = request.website

        if product_variant and website.enable_sales_visitor_count:
            fake_sales = website.fake_real_sales_count
            fake_visitors = website.fake_real_visitor_count
            cutoff_date = fields.Datetime.now() - datetime.timedelta(days=website.top_sold_duration_days or 30)

            sales_count = request.env['sale.order.line'].sudo().search_count([('create_date', '>=', cutoff_date),
                                                                              ('product_id', '=', product_variant.id),
                                                                              ('state', 'in', ('sale', 'done'))])

            res.update({'show_sales_visitor_count': True,
                        'total_sold': sales_count + fake_sales,
                        'visitor_count': product_variant.sudo().get_visitor_count() + fake_visitors})

        return res

    def shop_checkout(self, try_skip_step=None, **query_params):
        if request.website.enable_one_page_checkout:
            order_sudo = request.cart
            request.session['sale_last_order_id'] = order_sudo.id

            # CHECKOUT PAGE
            checkout_page_values = self._prepare_checkout_page_values(order_sudo, **query_params)

            if order_sudo._has_deliverable_products():
                available_dms = order_sudo._get_delivery_methods()
                checkout_page_values['delivery_methods'] = available_dms
                if delivery_method := order_sudo._get_preferred_delivery_method(available_dms):
                    rate = delivery_method.rate_shipment(order_sudo)
                    if (not order_sudo.carrier_id or not rate.get('success') or order_sudo.amount_delivery != rate[
                        'price']):
                        order_sudo._set_delivery_method(delivery_method, rate=rate)

            one_page_checkout_values = checkout_page_values

            # PAYMENT PAGE
            order_sudo._recompute_cart()

            payment_page_values = self._get_shop_payment_values(order_sudo, **query_params)
            payment_page_values['only_services'] = order_sudo and order_sudo.only_services

            if payment_page_values['errors']:
                payment_page_values.pop('payment_methods_sudo', '')
                payment_page_values.pop('tokens_sudo', '')

            payment_page_values.update(request.website._get_checkout_step_values())

            one_page_checkout_values.update(payment_page_values)

            payment_step = request.env['website.checkout.step'].sudo().search([('step_href', '=', '/shop/payment'),
                                                                               ('website_id', '=', request.website.id)],
                                                                              limit=1)

            one_page_checkout_values['current_website_checkout_step_href'] = payment_step.step_href
            one_page_checkout_values['previous_website_checkout_step'] = checkout_page_values[
                'previous_website_checkout_step']
            one_page_checkout_values['next_website_checkout_step'] = self.env['website.checkout.step'].sudo()
            one_page_checkout_values['next_website_checkout_step_href'] = False
            one_page_checkout_values['response_template'] = 'website_sale.payment'

            return request.render("theme_clarico_vega.one_page_checkout_payment", one_page_checkout_values)
        else:
            return super().shop_checkout(try_skip_step=try_skip_step, **query_params)


class WebsiteSaleWishlistEpt(WebsiteSaleWishlist):
    """
    Extension of Odoo's Website Sale Wishlist.
    """

    @http.route()
    def get_wishlist(self, count=False, **kw):
        """
        - Render collection of the current logged-in user
        - Filter out and render only wishes whose products are not available in the collections
        """
        res = super().get_wishlist(count=count, **kw)
        partner = request.env.user.sudo().partner_id
        collection_ids = request.env['wishlist.collection'].get_partner_collections(partner)
        if res.qcontext.get('wishes'):
            if collection_ids and collection_ids.product_line_ids:
                wishes = res.qcontext.get('wishes').filtered(
                    lambda
                        wish: wish.product_id.id not in collection_ids.product_line_ids.product_id.ids)
                res.qcontext['wishes'] = wishes
        res.qcontext['collections'] = collection_ids
        return res


class WebsiteSaleCartExt(WebsiteSaleCart):
    """
    Extension of Odoo's Website Sale Cart Class.
    """

    @route(
        route='/shop/cart/update',
        type='jsonrpc',
        auth='public',
        methods=['POST'],
        website=True,
        sitemap=False
    )
    def update_cart(self, line_id, quantity, product_id=None, **kwargs):
        # Call super to get the default values
        product_product = request.env['product.product'].browse(int(product_id))
        product_template = product_product.product_tmpl_id
        min_qty = product_template and product_template.min_order_qty
        if quantity and min_qty and quantity > 0 and min_qty and quantity < min_qty:
            quantity = min_qty

        values = super().update_cart(line_id, quantity, product_id=product_id, **kwargs)
        order_sudo = request.cart

        if order_sudo:
            currency = order_sudo.currency_id
            values['cart_total'] = float(order_sudo.amount_total)
            values['cart_currency'] = currency.symbol
            values['cart_currency_code'] = currency.name
            values['cart_currency_position'] = currency.position

            # Add/override the shorter_cart_summary key
        values['website_sale.shorter_cart_summary'] = request.env['ir.ui.view']._render_template(
            'website_sale.shorter_cart_summary', {'website_sale_order': order_sudo,
                                                  'show_shorter_cart_summary': True,
                                                  **self._get_express_shop_payment_values(order_sudo),
                                                  **request.website._get_checkout_step_values()}
        )
        return values

    @route()
    def add_to_cart(self, product_template_id, product_id, quantity=1.0, uom_id=None,
                    product_custom_attribute_values=None, no_variant_attribute_value_ids=None, linked_products=None,
                    **kwargs):
        product_template = request.env[_MODEL_PRODUCT_TEMPLATE].browse(int(product_template_id))
        min_qty = product_template and product_template.min_order_qty
        if quantity and min_qty and quantity > 0 and min_qty and quantity < min_qty:
            quantity = min_qty
        res = super().add_to_cart(product_template_id=product_template_id, product_id=product_id, quantity=quantity,
                                  uom_id=uom_id, product_custom_attribute_values=product_custom_attribute_values,
                                  no_variant_attribute_value_ids=no_variant_attribute_value_ids,
                                  linked_products=linked_products, **kwargs)
        return res

    @http.route(route='/shop/cart/quick_add', type='jsonrpc', auth='user', methods=['POST'], website=True)
    def quick_add(self, product_template_id, product_id, quantity=1.0, **kwargs):
        """ inherit of quick_add method to include cart summary details. .
            :return: dict
        """
        res = super().quick_add(product_template_id, product_id, quantity=quantity, **kwargs)

        order_sudo = request.cart

        if order_sudo:
            currency = order_sudo.currency_id
            res['cart_total'] = float(order_sudo.amount_total)
            res['cart_currency'] = currency.symbol
            res['cart_currency_code'] = currency.name
            res['cart_currency_position'] = currency.position

        return res
