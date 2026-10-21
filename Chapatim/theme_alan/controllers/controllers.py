# -*- coding: utf-8 -*-

import json
import ast
import odoo
import logging
import requests
import re
from markupsafe import Markup
from datetime import datetime, timedelta

from odoo.tools import lazy
from odoo import http, _, fields
from odoo.tools import format_amount
from odoo.http import request, route
from odoo.exceptions import UserError
from odoo.addons.web.controllers.home import Home
from odoo.addons.web.controllers.utils import ensure_db
from odoo.addons.website.controllers.main import Website
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.auth_oauth.controllers.main import OAuthLogin
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale.controllers.variant import WebsiteSaleVariantController
from odoo.addons.website_sale_comparison.controllers.main import WebsiteSaleProductComparison

_logger = logging.getLogger(__name__)
CREDENTIAL_PARAMS = ['login', 'password', 'type']

class WebsiteSaleAlanProductComparison(WebsiteSaleProductComparison):

    @route()
    def get_product_data(self, product_ids):
        """
        Extends the default product data route to include:
        - Active B2B mode
        - Public user status
        Returns a dictionary containing all these details.
        """
        res = super().get_product_data(product_ids=product_ids)
        if isinstance(res, list):
            for product_item in res:
                product_item.update({
                    'active_b2b_mode': request.website.active_b2b_mode,
                    'is_public_user': request.env.user._is_public(),
                })
                return res

class WebsiteSaleAlanVariant(WebsiteSaleVariantController):

    @route()
    def get_combination_info_website(self, *args, **kwargs):
        """
        Extends the default combination info route to include:
        - Product offer timing
        - Applicable pricelist rules
        - Current viewers count
        - Product sold count info
        Returns a dictionary containing all these details.
        """
        res = super().get_combination_info_website(*args, **kwargs)
        website = request.env['website'].get_current_website()
        current_pricelist = lazy(request.website._get_and_cache_current_pricelist)
        res.update({'bulk_save': False})
        product_id_val = res.get('product_id', 0)
        if not product_id_val:
            return res

        product = request.env['product.product'].sudo().browse(product_id_val)
        if not product.exists():
            return res

        # --- Pricelist and Offer Timing ---
        if current_pricelist:
            offer_data = product._get_offer_timing()
            pricelist_rules = current_pricelist.sudo()._get_applicable_rules(product, fields.Date.today())
            res.update({
                'product_offer_timer': offer_data,
                'product_pricelist_item_ids': [
                    {
                        'id': rule.id,
                        'min_quantity': rule.min_quantity,
                        'price': rule.sudo()._compute_price(product.sudo(), rule.min_quantity, product.uom_id.sudo(), date=datetime.today(), currency=website.currency_id),
                        'currency': rule.currency_id.symbol,
                    }
                    for rule in pricelist_rules
                ],
                'uom_name': product.uom_id.name,
            })

        # --- Current Viewers ---
        viewers_count = product._get_current_viewers()
        current_viewers_template = request.env['ir.ui.view']._render_template(
            'theme_alan.current_viewers', {'viewers_count': viewers_count}
        )

        # --- Product Sales Count ---
        product_sales_count = int(product.get_product_sale_count() or 0)

        # --- Get configurable time range for sales count ---
        params = request.env['ir.config_parameter'].sudo()
        time_range = params.get_param('atharva_theme_base.product_sales_count_time_range', 'last_month')
        time_range_map = {
            'yesterday': _('yesterday'),
            'this_week': _('this week'),
            'last_week': _('last week'),
            'this_month': _('this month'),
            'last_month': _('last month'),
        }
        time_range_str = time_range_map.get(time_range, _('last month'))

        # --- Render sold count info template ---
        sold_count_info_template = request.env['ir.ui.view']._render_template(
            'theme_alan.as_product_sold_count_info',
            {'product_count': product_sales_count, 'time_range_str': time_range_str}
        )

        # --- Update final response ---
        res.update({
            'default_code': product.default_code,
            'current_viewers': current_viewers_template,
            'product_sold_count_info': sold_count_info_template,
            'active_b2b_mode': request.website.active_b2b_mode,
            'is_public_user': request.env.user._is_public(),
            'barcode':product.barcode,
            'active_product_brand': bool(website.active_product_brand and product.product_brand_id),
            'active_product_advance_info': bool(website.active_product_advance_info and len(product.product_offer_ids)>0),
            'active_product_category': bool(website.active_product_category and product.public_categ_ids),
            'active_product_reference': bool(website.active_product_reference and product.default_code),
            'active_shop_product_barcode': bool(website.active_shop_product_barcode and product.barcode),
        })

        return res

class WebsiteSaleAlanController(WebsiteSale):

    @route()
    def product(self, product, category=None, pricelist=None, **kwargs):
        """ Extends the default product route """
        res = super(WebsiteSaleAlanController, self).product(product, category, pricelist, **kwargs)
        res.qcontext.update({'as_product_detail': True})

        domain = request.website.sale_product_domain() + [
            ('active', '=', True),
            ('website_published', '=', True)
        ]

        # --- Get next product ---
        next_product = product.search(
            domain + [('website_sequence', '>', product.website_sequence)],
            order='website_sequence ASC',
            limit=1
        )

        # --- Get previous product ---
        previous_product = product.search(
            domain + [('website_sequence', '<', product.website_sequence)],
            order='website_sequence DESC',
            limit=1
        )

        res.qcontext.update({
            'next_product': next_product or False,
            'previous_product': previous_product or False,
        })
        return res

    @http.route(['/product_queries'], auth='public', type='jsonrpc', website=True, cors='*')
    def product_queries(self, **kw):
        user = request.env.user.sudo()
        partner = user.partner_id[:1]
        now = fields.Datetime.now()

        product_id = kw.get('product_id')

        if isinstance(product_id, (list, tuple)):
            product_id = product_id[0]

        try:
            product_id = int(product_id)
        except Exception:
            return False

        product_obj = request.env['product.product'].sudo().browse(product_id)
        product = product_obj.product_tmpl_id if product_obj.exists() else request.env['product.template'].sudo().browse(product_id)
        if not product.exists():
            return False

        try:
            inquiry_data = ast.literal_eval(user.inquiry_data or '{}')
        except Exception:
            inquiry_data = {}

        # --- Public users are not uniquely identifiable — always allow popup ---
        if not user._is_public():
            key = str(product.id)

            # --- CHECK 24H BLOCK (logged-in users only) ---
            existing_list = inquiry_data.get(key, [])

            if not isinstance(existing_list, list):
                existing_list = []

            for dt_str in existing_list:
                try:
                    stored_dt = fields.Datetime.from_string(dt_str)
                    # --- 24H Block ---
                    if stored_dt + timedelta(hours=24) > now:
                        return {'allow': False}

                except Exception:
                    continue

        if not user._is_public() and (partner.email or partner.phone):
            time_24h_ago = now - timedelta(hours=24)
            domain = [
                ('create_date', '>=', time_24h_ago),
                ('name', 'ilike', f'[PID:{product.id}] %'),
            ]
            final_or_filters = []
            if partner.email:
                final_or_filters.append(('email_from', '=', partner.email))
            if partner.phone:
                final_or_filters.append(('phone', '=', partner.phone))
                final_or_filters.append(('description', 'ilike', '%' + partner.phone + '%'))
            if not user._is_public():
                final_or_filters.append(('partner_id', '=', partner.id))

            if final_or_filters:
                for i in range(len(final_or_filters) - 1):
                    domain.append('|')
                domain.extend(final_or_filters)
                if request.env['crm.lead'].sudo().search_count(domain):
                    return {'allow': False}

        res_data = {
            'allow': True,
            'user_id': partner.id,
            'user_name': partner.name or '',
            'user_email': partner.email or '',
            'user_phone': partner.phone or '',
            'is_public_user': user._is_public(),
            'dialog_header': request.website.inquiry_header,
            'dialog_header_desc': request.website.inquiry_desc_info,
            'acknowledgement_message': request.website.acknowledgement_message,
        }
        # --- PREVENT CACHING ---
        request.future_response.headers.set('Cache-Control', 'no-cache, no-store, must-revalidate')
        request.future_response.headers.set('Pragma', 'no-cache')
        request.future_response.headers.set('Expires', '0')
        return res_data

    @http.route(['/send_queries_mail'], auth='public', type='jsonrpc', website=True, cors='*')
    def product_queries_send_mail(self, **kw):

        product_id = kw.get('product_id')
        user_name = kw.get('customer_name')
        user_email = (kw.get('email') or '').strip().lower()
        user_phone = (kw.get('phone') or '').strip()
        user_question = kw.get('message')
        contact_preference = kw.get('contact_preference')


        # --- Validation ---
        if isinstance(product_id, (list, tuple)):
            product_id = product_id[0]

        try:
            product_id = int(product_id)
        except Exception:
            return {'success': False, 'message': 'Invalid product.'}
        product_obj = request.env['product.product'].sudo().browse(product_id)
        product = product_obj.product_tmpl_id if product_obj.exists() else request.env['product.template'].sudo().browse(product_id)
        if not product.exists():
            return {'success': False, 'message': 'Product no longer exists.'}

        time_limit = fields.Datetime.now() - timedelta(hours=24)
        domain = [
            ('create_date', '>=', time_limit),
            ('name', 'ilike', f'[PID:{product.id}] %'),
        ]
        final_or_filters = []
        if user_email:
            final_or_filters.append(('email_from', '=', user_email))
        if user_phone:
            # Normalize phone (digits only) for search
            clean_phone = re.sub(r'\D', '', user_phone)
            if clean_phone:
                final_or_filters.append(('phone', 'ilike', '%' + clean_phone + '%'))
            final_or_filters.append(('description', 'ilike', '%' + user_phone + '%'))
        user_id = kw.get('user_id')
        if isinstance(user_id, list):
            user_id = user_id[0]
        partner = request.env['res.partner'].sudo().browse(user_id)[:1]

        if not request.env.user._is_public():
            final_or_filters.append(('partner_id', '=', partner.id))

        if final_or_filters:
            for i in range(len(final_or_filters) - 1):
                domain.append('|')
            domain.extend(final_or_filters)
            if request.env['crm.lead'].sudo().search_count(domain):
                return {
                    'success': False,
                    'error_code': 'already_submitted',
                }

        # ---  Prepare Data ---
        template = request.env.ref(
            'theme_alan.email_template_product_queries',
            raise_if_not_found=False
        )

        res_config = request.website.inquiry_submit_action

        # Build contact preference label and dynamic body fields
        original_preference = contact_preference
        if contact_preference == 'Both':
            contact_preference = 'Email OR Phone'

        crm_body = (
            '<h3>Product Inquiry - Your Assistance Needed</h3><br/>'
            '<div>Product Name : %s</div>'
            '<div>Question : %s</div>'
            '<div>Contact Preference : %s</div>'
        )
        crm_args = [product.name, user_question, contact_preference]

        if original_preference in ('Email', 'Both'):
            crm_body += '<div>Email : %s</div>'
            crm_args.append(user_email or '-')
        if original_preference in ('Phone', 'Both'):
            crm_body += '<div>Phone : %s</div>'
            crm_args.append(user_phone or '-')

        crm_description = Markup(crm_body) % tuple(crm_args)

        # --- Create CRM Lead (Always create if valid, to support restriction) ---
        sales_team = request.website.sales_team_id
        sales_person = request.website.sales_person_id

        lead_vals = {
            'name': f'[PID:{product.id}] Product Inquiry: {product.name}',
            'contact_name': user_name,
            'email_from': user_email,
            'phone': user_phone,
            'partner_id': partner.id if not request.env.user._is_public() else False,
            'description': crm_description,
        }
        if sales_team:
            lead_vals['team_id'] = sales_team.id
        if sales_person:
            lead_vals['user_id'] = sales_person.id

        request.env['crm.lead'].sudo().create(lead_vals)

        # --- Send Email ---
        if template and res_config == 'email':
            recipient_user = request.website.sudo().inquiry_recipient_id

            composer = request.env['mail.compose.message'].sudo().with_context(
                message=user_question,
                product=product.name,
                partner_name=user_name or recipient_user.partner_id.name,
                contact_preference=contact_preference,
                default_force_send=True,
                default_composition_mode='mass_mail',
                default_model='res.partner',
                default_res_ids=recipient_user.partner_id.ids,
                default_template_id=template.id,
                email_to=recipient_user.partner_id.email,
                default_is_queries_mail=True,
                phone=user_phone,
                sender_email=user_email,
            ).create({
                'message_type': 'comment',
            })

            composer._action_send_mail()

        # --- UPDATE inquiry_data for logged-in users
        user = request.env.user.sudo()
        if not user._is_public():
            try:
                inquiry_data = ast.literal_eval(user.inquiry_data or '{}')
            except Exception:
                inquiry_data = {}
            key = str(product.id)
            if key not in inquiry_data or not isinstance(inquiry_data[key], list):
                inquiry_data[key] = []
            inquiry_data[key].append(fields.Datetime.to_string(fields.Datetime.now()))
            user.sudo().write({'inquiry_data': str(inquiry_data)})

        return {
            'success': True,
            'message': request.website.acknowledgement_message or "Your inquiry has been sent successfully."
        }


    @route('/advance/info/editor/<model("as.product.extra.info"):offer>', auth='user', type='http', website=True, cors='*')
    def advance_info_dialog_design(self, offer):
        """ Render the advance info dialog design """
        return request.render('theme_alan.as_product_advance_info_design', {'layout': offer})

    @route('/get_advance_info', auth='public', type='jsonrpc', website=True, cors='*')
    def get_advance_info(self, advance_info_id):
        """ Get the advance info for the product """
        offer = request.env['as.product.extra.info'].sudo().search([('id','=',advance_info_id)], limit=1)
        if offer.detail_description:
            return offer.detail_description
        return ''

    @http.route('/shop/check_zip_code', type='jsonrpc', auth='public', methods=['POST'], website=True)
    def check_zip_code(self, zip_code, **kwargs):
        """ Check the zip code for the carrier """
        try:
            zip_code = zip_code.strip()
            carriers = request.env['delivery.carrier'].sudo().search([('active', '=', True)])
            allowed_countries = []
            allowed_states = {}

            for carrier in carriers:
                if carrier.country_ids:
                    for country in carrier.country_ids:
                        country_name = country.name.lower().strip()
                        allowed_countries.append(country_name)
                        # --- Check if carrier has state restrictions for this country ---
                        if carrier.state_ids:
                            states = carrier.state_ids.filtered(lambda s: s.country_id.id == country.id)
                            if states:
                                if country_name not in allowed_states:
                                    allowed_states[country_name] = []
                                allowed_states[country_name].extend([s.name.lower().strip() for s in states])

            allowed_countries = list(set(allowed_countries))
            # --- Use OpenStreetMap Nominatim API via HTTP request (free, no library needed) ---
            try:
                url = "https://nominatim.openstreetmap.org/search"
                params = {
                    'postalcode': zip_code,
                    'format': 'json',
                    'timeout': 10
                }
                headers = {'User-Agent': 'Odoo-Shop-Delivery-Checker/1.0'}
                response = requests.get(url, params=params, headers=headers, timeout=10)
                response.raise_for_status()
                results = response.json()

                if results:
                    location = results[0]
                    address = location.get('address', {})

                    # --- Extract country and state from address ---
                    country_name = address.get('country', '').lower().strip()
                    state_name = address.get('state', '').lower().strip()
                    place_name = address.get('city') or address.get('town') or address.get('village') or 'this area'

                    if country_name in allowed_countries:
                        if country_name in allowed_states:
                            if state_name in allowed_states[country_name]:
                                return {
                                    'message': f'Delivery Available to {place_name}',
                                    'css_class': 'text-success'
                                }
                            else:
                                return {
                                    'message': 'Delivery not available to this area',
                                    'css_class': 'text-danger'
                                }
                        else:
                            return {
                                'message': f'Delivery Available to {place_name}',
                                'css_class': 'text-success'
                            }

                return {
                    'message': 'Delivery not available to this area',
                    'css_class': 'text-danger'
                }

            except (requests.RequestException, ValueError):
                return {
                    'message': 'Unable to verify delivery for this area',
                    'css_class': 'text-warning'
                }

        except Exception as e:
            return {
                'message': 'Error checking delivery availability',
                'css_class': 'text-danger'
            }

class AlanShops(http.Controller):

    @route(['/shop/brands', '/shop/brands/page/<int:page>'], type='http', auth="public", website=True)
    def BrandPage(self, page=0, brand_search='', sort=''):
        """ This method is used to display the brand page. """
        brand_search = brand_search.strip()
        domain = ['&', ('active', '=', True), ('website_id', 'in', (False, request.website.id))]

        # --- Add search filter ---
        if brand_search:
            domain.append(('name', 'ilike', brand_search))

        # --- Add sort filter ---
        if sort == 'best_seller':
            from_date = 182
            product_env = request.env['product.template']
            bs_records = product_env._get_best_seller_product(
                from_date, request.website.id, limit=10
            )
            brand_ids = bs_records.mapped('product_brand_id').ids
            if brand_ids:
                domain.append(('id', 'in', brand_ids))
            brands = request.env['as.product.brand'].sudo().search(domain)

        else:
            order = "name asc"
            if sort == 'name_desc':
                order = "name desc"
            elif sort == 'recently_added':
                order = "create_date desc"
            brands = request.env['as.product.brand'].sudo().search(domain, order=order)

        pager = request.website.pager(
            url='/shop/brands',
            total=len(brands),
            page=page,
            step=30,
        )
        offset = pager['offset']
        brands = brands[offset: offset + 30]
        available_letters = sorted(set((b.name or '').strip()[0].upper() for b in brands if b.name))

        return request.render("theme_alan.brand_list", {'brands': brands,'pager': pager,'brand_search': brand_search,'sort': sort,'available_letters': available_letters})

    @route('/get_mini_cart', auth='public', type='jsonrpc', website=True, cors='*')
    def mini_cart(self, **post):
        """ This method is used to display the mini cart. """
        order = request.cart
        if not order:
            return {
                'cart_quantity': 0,
                'website_order_lines': [],
                'suggested_products': [],
                'cart_summary': {},
                'claimable_rewards': [],
            }

        currency = order.currency_id or request.env.company.currency_id
        format_amount_currency = lambda amount: format_amount(request.env, amount, currency)
        as_free_shipping_details = order.sudo().get_shipping_details()

        def format_product_line(line):
            return {
                'line_id': line.id,
                'product_id': line.product_id.id,
                'product_tmp_id': line.product_id.product_tmpl_id.id,
                'image_url': f'/web/image/product.product/{line.product_id.id}/image_128',
                'website_url': line.product_id.website_url,
                'product_uom_qty': line.product_uom_qty,
                'description_lines': list(line.get_description_following_lines()),
                'combination_name': line._get_combination_name(),
                'has_multiple_uoms': line.product_template_id._has_multiple_uoms(),
                'product_uom': line.product_uom_id.name,
                'line_header': line._get_line_header(),
                'is_sellable': line._is_sellable(),
                'is_reward_line': line.is_reward_line,
                'reward_type': line.reward_id.reward_type if line.reward_id else None,
                'show_strikethrough_price': line._should_show_strikethrough_price(),
                'strikethrough_price':format_amount_currency(line._get_displayed_unit_price() * line.product_uom_qty),
                'formated_product_price': format_amount_currency(line._get_cart_display_price()),
            }

        def format_suggested_product_line(prod):
            combination = prod._get_combination_info_variant()
            return {
                'product_id': prod.id,
                'product_tmpl_id': prod.product_tmpl_id.id,
                'product_name': prod.display_name,
                'has_discounted_price': combination['has_discounted_price'],
                'list_price': format_amount_currency(combination['list_price']),
                'price': format_amount_currency(combination['price']),
                'image_url': f'/web/image/product.product/{prod.id}/image_512',
                'website_url': prod.website_url,
            }

        cart_summary = {
            'reward_amount': format_amount_currency(order.reward_amount) if order.reward_amount else 0,
            'carrier_id': order.carrier_id.id,
            'amount_delivery': format_amount_currency(order.amount_delivery),
            'amount_untaxed': format_amount_currency(order.amount_untaxed),
            'amount_tax': format_amount_currency(order.amount_tax),
            'amount_total': format_amount_currency(order.amount_total),
            'shipping_detail': {},
        }

        if as_free_shipping_details:
            cart_summary.update({
                'shipping_detail': {
                    'any_ns_product': as_free_shipping_details['any_ns_product'],
                    'carries_amount': as_free_shipping_details['carries_amount'],
                    'total_amount': as_free_shipping_details['total_amount'],
                    'status': as_free_shipping_details['status'],
                    'pending_amount': format_amount(request.env, as_free_shipping_details['pending_amount'], currency),
                    'active_free_shipping': request.website.active_free_shipping,
                }
            })

        claimable_rewards = []
        try:
            rewards_dict = order._get_claimable_and_showable_rewards()
            for coupon_obj, rewards in rewards_dict.items():
                coupon_data = {
                    'id': coupon_obj.id,
                    'code': coupon_obj.code,
                    'point_name': getattr(coupon_obj, 'point_name', ''),
                    'points': order._get_real_points_for_coupon(coupon_obj) if hasattr(order, '_get_real_points_for_coupon') else 0,
                    'expiration_date': coupon_obj.expiration_date.strftime('%Y-%m-%d') if coupon_obj.expiration_date else None,
                    'currency':order.currency_id.symbol,
                }

                rewards_data = []
                for reward in rewards:
                    reward_data = {
                        'id': reward.id,
                        'description': reward.description or '',
                        'currency': currency.symbol,
                        'multi_product': reward.multi_product,
                        'required_points': reward.required_points,
                        'reward_type': reward.reward_type,
                        'program_id': {
                            'id': reward.program_id.id,
                            'program_type': reward.program_id.program_type,
                            'trigger': reward.program_id.trigger,
                            'applies_on': reward.program_id.applies_on,
                            'portal_visible': reward.program_id.portal_visible,
                            'is_nominative': reward.program_id.is_nominative,
                        },
                        'reward_product_ids': []
                    }

                    if reward.multi_product:
                        reward_data['reward_product_ids'] = [
                            {
                                'id': product.id,
                                'display_name': product.display_name,
                            }
                            for product in reward.reward_product_ids
                        ]

                    rewards_data.append(reward_data)

                claimable_rewards.append([coupon_data, rewards_data])
        except Exception as e:
            _logger.error(f"Error getting claimable rewards: {e}")

        context = {
            'cart_quantity': order.cart_quantity,
            'website_order_lines': [format_product_line(l) for l in order.website_order_line],
            'suggested_products': [format_suggested_product_line(p) for p in order.sudo()._cart_accessories()],
            'cart_summary': cart_summary,
            'code_not_available': post.get('code_not_available', 1),
            'claimable_rewards': claimable_rewards,
        }
        return context

    @route('/apply_coupon', auth='public', type='jsonrpc', website=True, cors='*')
    def apply_coupon(self, promo, **post):
        """ This method is used to apply the coupon code in MiniCart """
        order = request.cart
        if not order:
            return {
                'error': 'No active cart found',
                'promo_error': 'No active cart found',
                'promo_success': False,
                'website_sale_order': {
                    'promo_error': 'No active cart found',
                    'promo_success': False,
                    'claimable_rewards': [],
                },
            }

        try:
            result = order._try_apply_code(promo)
            _logger.info(f"Apply code result: {result}")

            if result.get('error'):
                return {
                    'error': result['error'],
                    'promo_error': result['error'],
                    'promo_success': False,
                    'website_sale_order': {
                        'promo_error': result['error'],
                        'promo_success': False,
                        'claimable_rewards': [],
                    },
                }
            success_msg = order.get_promo_code_success_message(delete=False)
            error_msg = order.get_promo_code_error(delete=False)
            _logger.info(f"Success message: {success_msg}, Error message: {error_msg}")
            claimable_rewards = []
            try:
                rewards_dict = order._get_claimable_and_showable_rewards()
                _logger.info(f"Rewards dict: {rewards_dict}")

                for coupon_obj, rewards in rewards_dict.items():
                    coupon_data = {
                        'id': coupon_obj.id,
                        'code': coupon_obj.code,
                        'point_name': getattr(coupon_obj, 'point_name', ''),
                        'points': order._get_real_points_for_coupon(coupon_obj) if hasattr(order, '_get_real_points_for_coupon') else 0,
                        'expiration_date': coupon_obj.expiration_date.strftime('%Y-%m-%d') if coupon_obj.expiration_date else None,
                    }

                    rewards_data = []
                    for reward in rewards:
                        reward_data = {
                            'id': reward.id,
                            'description': reward.description or '',
                            'multi_product': reward.multi_product,
                            'required_points': reward.required_points,
                            'reward_type': reward.reward_type,
                            'program_id': {
                                'id': reward.program_id.id,
                                'program_type': reward.program_id.program_type,
                                'trigger': reward.program_id.trigger,
                                'applies_on': reward.program_id.applies_on,
                                'portal_visible': reward.program_id.portal_visible,
                                'is_nominative': reward.program_id.is_nominative,
                            },
                            'reward_product_ids': []
                        }

                        if reward.multi_product:
                            reward_data['reward_product_ids'] = [
                                {
                                    'id': product.id,
                                    'display_name': product.display_name,
                                }
                                for product in reward.reward_product_ids
                            ]
                        rewards_data.append(reward_data)
                    claimable_rewards.append([coupon_data, rewards_data])
                _logger.info(f"Claimable rewards: {claimable_rewards}")
            except Exception as e:
                _logger.error(f"Error getting claimable rewards: {e}")

            return {
                'error': False,
                'promo_error': error_msg if error_msg else False,
                'promo_success': success_msg if success_msg else promo,
                'promo_code': promo,
                'website_sale_order': {
                    'promo_error': error_msg if error_msg else False,
                    'promo_success': success_msg if success_msg else promo,
                    'claimable_rewards': claimable_rewards,
                    'reward_amount': order.reward_amount if hasattr(order, 'reward_amount') else 0,
                },
            }

        except Exception as e:
            _logger.error(f"Error applying coupon: {e}", exc_info=True)
            return {
                'error': str(e),
                'promo_error': str(e),
                'promo_success': False,
                'website_sale_order': {
                    'promo_error': str(e),
                    'promo_success': False,
                    'claimable_rewards': [],
                }
            }

    @route('/claim_reward', auth='public', type='jsonrpc', website=True, cors='*')
    def claim_reward(self, reward_id, code=None, product_id=None, **post):
        """ This method is used to claim the reward in MiniCart """
        order = request.cart
        if not order:
            return {
                'error': 'No active cart found',
                'success': False,
                'website_sale_order': {
                    'claimable_rewards': [],
                    'reward_amount': 0,
                }
            }

        try:
            reward_id = int(reward_id)
        except (ValueError, TypeError):
            return {
                'error': 'Invalid reward ID',
                'success': False,
                'website_sale_order': {
                    'claimable_rewards': [],
                    'reward_amount': 0,
                }
            }

        reward_sudo = request.env['loyalty.reward'].sudo().browse(reward_id).exists()
        if not reward_sudo:
            return {
                'error': 'Reward not found',
                'success': False,
                'website_sale_order': {
                    'claimable_rewards': [],
                    'reward_amount': 0,
                }
            }

        if reward_sudo.multi_product and product_id:
            request.update_context(product_id=int(product_id))

        claimable_rewards = order._get_claimable_and_showable_rewards()
        coupon = request.env['loyalty.card']

        for coupon_, rewards in claimable_rewards.items():
            if reward_sudo in rewards:
                coupon = coupon_
                break

        if not coupon:
            return {
                'error': 'Coupon not found for this reward',
                'success': False,
                'website_sale_order': {
                    'claimable_rewards': [],
                    'reward_amount': 0,
                }
            }

        product = None
        if request.env.context.get('product_id'):
            product = request.env['product.product'].sudo().browse(request.env.context.get('product_id'))

        try:
            reward_status = order._apply_program_reward(reward_sudo, coupon, product=product)
        except UserError as e:
            return {
                'error': str(e),
                'success': False,
                'website_sale_order': {
                    'claimable_rewards': [],
                    'reward_amount': order.reward_amount if hasattr(order, 'reward_amount') else 0,
                }
            }

        if 'error' in reward_status:
            return {
                'error': reward_status['error'],
                'success': False,
                'website_sale_order': {
                    'claimable_rewards': [],
                    'reward_amount': order.reward_amount if hasattr(order, 'reward_amount') else 0,
                }
            }

        # --- Update programs and rewards ---
        order._update_programs_and_rewards()

        # --- Update shipping if necessary ---
        if order.carrier_id.free_over and not reward_sudo.program_id.is_payment_program:
            res = order.carrier_id.rate_shipment(order)
            if res.get('success'):
                order.set_delivery_line(order.carrier_id, res['price'])
            else:
                order._remove_delivery_line()

        # --- Get updated claimable rewards after applying ---
        updated_claimable_rewards = []
        try:
            rewards_dict = order._get_claimable_and_showable_rewards()
            # --- Convert to serializable format ---
            for coupon_obj, rewards in rewards_dict.items():
                coupon_data = {
                    'id': coupon_obj.id,
                    'code': coupon_obj.code,
                    'point_name': getattr(coupon_obj, 'point_name', ''),
                    'points': order._get_real_points_for_coupon(coupon_obj) if hasattr(order, '_get_real_points_for_coupon') else 0,
                    'expiration_date': coupon_obj.expiration_date.strftime('%Y-%m-%d') if coupon_obj.expiration_date else None,
                }

                rewards_data = []
                for reward in rewards:
                    reward_data = {
                        'id': reward.id,
                        'description': reward.description or '',
                        'multi_product': reward.multi_product,
                        'required_points': reward.required_points,
                        'reward_type': reward.reward_type,
                        'program_id': {
                            'id': reward.program_id.id,
                            'program_type': reward.program_id.program_type,
                            'trigger': reward.program_id.trigger,
                            'applies_on': reward.program_id.applies_on,
                            'portal_visible': reward.program_id.portal_visible,
                            'is_nominative': reward.program_id.is_nominative,
                        },
                        'reward_product_ids': []
                    }

                    if reward.multi_product:
                        reward_data['reward_product_ids'] = [
                            {
                                'id': product.id,
                                'display_name': product.display_name,
                            }
                            for product in reward.reward_product_ids
                        ]

                    rewards_data.append(reward_data)

                updated_claimable_rewards.append([coupon_data, rewards_data])
        except Exception as e:
            _logger.error(f"Error getting updated claimable rewards: {e}")

        return {
            'error': False,
            'success': True,
            'message': f'Reward "{reward_sudo.description}" applied successfully',
            'website_sale_order': {
                'claimable_rewards': updated_claimable_rewards,
                'reward_amount': order.reward_amount if hasattr(order, 'reward_amount') else 0,
            }
        }

    @route('/as_clear_cart', auth='public', type='jsonrpc', website=True, cors='*')
    def as_clear_cart(self, **kw):
        """ This method is used to clear the cart in MiniCart """
        order = request.cart
        request.session['website_sale_cart_quantity'] = 0
        order.unlink()

    @route('/get_quick_view_template', type='jsonrpc', auth='public', website=True, cors='*')
    def get_quick_view(self, **kw):
        """ This method is used to get the quick view template in Shop Page """
        product = request.env['product.template'].sudo().browse(kw.get('product_id'))
        return request.env['ir.ui.view']._render_template('theme_alan.as_quick_view_model', {'product': product})

    @http.route('/shop/get_product_variants', type='jsonrpc', auth='public', website=True)
    def get_product_variants(self, product_template_id, **kwargs):
        """ This method is used to get the product variants in Shop Page """
        product_tmpl = request.env['product.template'].sudo().browse(int(product_template_id))
        website = request.website
        pricelist = website._get_and_cache_current_pricelist()
        currency = pricelist.currency_id

        if not product_tmpl.exists():
            return {'variants': []}

        variants = []

        for variant in product_tmpl.product_variant_ids.filtered('active'):
            combination = product_tmpl._get_combination_info(
                combination=variant.product_template_attribute_value_ids,
                product_id=variant.id,
                add_qty=1,
            )

            image = (
                f'/web/image/product.product/{variant.id}/image_512'
                if variant.image_1920
                else f'/web/image/product.template/{product_tmpl.id}/image_512'
            )

            free_qty = sum(website._get_product_available_qty(prod) for prod in variant.sudo())
            in_stock = variant.sudo().allow_out_of_stock_order or free_qty >= 1

            variants.append({
                'id': variant.id,
                'name': ' - '.join(variant.product_template_attribute_value_ids.mapped('name')) or variant.name,
                'image': image,
                'url': f'{product_tmpl.website_url}?variant={variant.id}',
                'price': f"{currency.symbol} {combination['price']}",
                'list_price': f"{currency.symbol} {combination['list_price']}",
                'has_discount': combination['has_discounted_price'],
                'discount_percent': combination.get('as_offer_discount', 0),
                'in_stock': in_stock,
            })

        return {'variants': variants}

class LoginPopup(Home):

    @route('/get_login_popup', type='jsonrpc', auth='public', website=True)
    def alan_login_popup(self, **kwargs):
        """ This method is used to get the login popup. """
        context = {}
        providers = OAuthLogin.list_providers(self)
        context.update(super().get_auth_signup_config())
        context.update({'providers':providers})
        signup_enabled = request.env['res.users']._get_signup_invitation_scope() == 'b2c'
        reset_password_enabled = request.env['ir.config_parameter'].sudo().get_param('auth_signup.reset_password') == 'True'
        website_logo = request.website.image_url(request.website,'logo')
        context.update({'signup_enabled':signup_enabled ,'reset_password_enabled':reset_password_enabled,'website_logo':website_logo,'active_b2b_signup': request.website.active_b2b_signup, 'active_b2b_mode': request.website.active_b2b_mode})

        return context

    @route('/alan/login/authenticate', type='jsonrpc', auth='none')
    def alan_login_authenticate(self, **kwargs):
        """ This method is used to authenticate the user in login popup. """
        ensure_db()
        request.params['login_success'] = False

        if not request.env.uid:
            request.update_env(user=odoo.SUPERUSER_ID)

        values = request.params.copy()
        if request.httprequest.method == 'POST':
            try:
                credential = {key: value for key, value in request.params.items() if key in CREDENTIAL_PARAMS}
                credential.setdefault('type', 'password')
                env = request.env
                auth_info = request.session.authenticate(env, credential)

                request.params['login_success'] = True
                request.redirect(self._login_redirect(auth_info['uid'], redirect=None))
                return request.params

            except odoo.exceptions.AccessDenied as e:
                if e.args == odoo.exceptions.AccessDenied().args:
                    values['error'] = _('Wrong login/password')
                else:
                    values['error'] = e.args[0]

        if 'login' not in values and request.session.get('auth_login'):
            values['login'] = request.session.get('auth_login')

        return values

    @route('/alan/signup/authenticate', type='jsonrpc', auth='public')
    def alan_signup_authenticate(self,*args, **kw):
        ''' Signup Authentication '''
        qcontext = super(LoginPopup,self).get_auth_signup_qcontext()
        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                super(LoginPopup,self).do_signup(qcontext)
                User = request.env['res.users']

                user_sudo = User.sudo().search(
                    User._get_login_domain(qcontext.get('login')), order=User._get_login_order(), limit=1
                )
                template = request.env.ref('auth_signup.mail_template_user_signup_account_created', raise_if_not_found=False)
                if user_sudo and template:
                    template.sudo().send_mail(user_sudo.id, force_send=True)
                return {'signup_success':True}
            except UserError as e:
                qcontext['error'] = e.args[0]
            except (SignupError, AssertionError) as e:
                if request.env['res.users'].sudo().search([('login', '=', qcontext.get('login'))]):
                    qcontext['error'] = _('Another user is already registered using this email address.')
                else:
                    _logger.error('%s', e)
                    qcontext['error'] = _('Could not create a new account.')
        return qcontext

class B2BWebsite(Website):

    @route()
    def autocomplete(self, search_type=None, term=None, order=None, limit=5, max_nb_chars=999, options=None):
        """ This method is used to search for products, brands, tags, and parent categories. """
        result = super().autocomplete(search_type, term, order, limit, max_nb_chars, options)
        if request.env.user._is_public() and request.website.active_b2b_mode:
            result['parts']['is_b2b_mode'] = True
        else:
            result['parts']['is_b2b_mode'] = False
        return result

    @route()
    def hybrid_list(self, page=1, search='', search_type='all', **kw):
        """ This method is used to search for products, brands, tags, and parent categories. """
        result = super().hybrid_list(page, search, search_type, **kw)
        if request.env.user._is_public() and request.website.active_b2b_mode:
            result.qcontext['is_b2b_mode'] = True
        else:
            result.qcontext['is_b2b_mode'] = False
        return result


class AlanWebsiteSearch(Website):

    @http.route()
    def autocomplete(self, search_type=None, term=None, order=None, limit=5, max_nb_chars=999, options=None):
        """ This method is used to search for products, brands, tags, and parent categories. """
        res = super(AlanWebsiteSearch, self).autocomplete(
            search_type=search_type,
            term=term,
            order=order,
            limit=limit,
            max_nb_chars=max_nb_chars,
            options=options
        )
        if search_type == "as_advance_search":
            brands = []
            tags = []
            parent_categories = []
            sub_categories = []
            products = []
            exact_match = None

            if term:
                brand_domain = [('active', '=', True), ('name', 'ilike', term)]
                brand_records = request.env['as.product.brand'].sudo().search(brand_domain, limit=limit)

                for brand in brand_records:
                    brand_data = {
                        '_fa': 'brand',
                        'id': brand.id,
                        'name': brand.name,
                        'website_url': f"/shop?brands={brand.id}",
                        'type': 'brand',
                    }
                    brands.append(brand_data)
                    if brand.name and not exact_match:
                        exact_match = brand_data

            for rec in res.get('results', []):
                fa_icon = rec.get('_fa', '')

                if fa_icon == 'brand':
                    continue

                elif fa_icon == 'tag':
                    tags.append(rec)

                elif fa_icon == 'fa-folder-o':
                    if rec.get('parent_id'):
                        sub_categories.append(rec)
                    else:
                        parent_categories.append(rec)

                    if term and rec.get('name', '') and not exact_match :
                        rec['type'] = 'category'
                        exact_match = rec

                else:
                    products.append(rec)

            res.update({
                'brands': brands,
                'tags': tags,
                'parent_categories': parent_categories,
                'sub_categories': sub_categories,
                'products': products,
                'exact_match': exact_match,
            })

        return res