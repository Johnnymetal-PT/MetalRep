# -*- coding: utf-8 -*-
""" Inherit the website model to add fields """

import base64
import json
import werkzeug.urls
import werkzeug.utils

from odoo.http import request
from odoo.exceptions import ValidationError
from odoo import fields, models, tools, api, _
from urllib.parse import urlparse, parse_qs
from odoo.addons.auth_oauth.controllers.main import OAuthLogin


class Website(models.Model):
    """ Inherit the website model"""

    _inherit = "website"

    # Advanced search
    enable_smart_search = fields.Boolean(
        string="Advanced Search", default=True,
        help="Enable it to activate search synonyms and search keywords reporting.")
    search_in_brands = fields.Boolean(string="Search with Brands", default=True)
    search_in_attributes_and_values = fields.Boolean(string="Search with Attributes", default=True)

    # Allow selected countries
    allow_countries = fields.Many2many('res.country', string='Allow Countries')
    default_country_id = fields.Many2one('res.country', string='Default Country',
                                         domain="[('id','in',allow_countries)]")

    is_free_shipping = fields.Boolean(string="Display free shipping offer in cart", default=False)
    free_shipping_price = fields.Integer('Free Shipping Price')
    is_card_layout = fields.Boolean('Display the product card layout.', default=False)

    # Lazy Load
    is_lazy_load = fields.Boolean(string='Lazyload', help="Lazy load will be enabled")
    lazy_load_image = fields.Binary('Lazyload Image', help="Display this image while lazy load applies.")

    # Load More
    is_load_more = fields.Boolean(string='Load More', help="Load more will be enabled")
    load_more_image = fields.Binary('Load More Image', help="Display this image while load more applies.")
    button_or_scroll = fields.Selection([
        ('automatic', 'Automatic- on page scroll'),
        ('button', 'Button- on click button')
    ], string="Loading type for products", required=True, default='automatic')
    prev_button_label = fields.Char(string='Label for the Prev Button',
                                    default="Load prev", translate=True)
    next_button_label = fields.Char(string='Label for the Next Button',
                                    default="Load next", translate=True)

    # OUT of STOCK settings
    option_out_of_stock = fields.Boolean('Display Label on Out of Stock Products',
                                         help="If Yes, then message/text will be displayed for out of stock products "
                                              "on shop page")
    text_out_of_stock = fields.Char('Out of Stock Label Text', default='OUT OF STOCK', translate=True)
    display_out_of_stock = fields.Boolean('Display Out of Stock Products', default=True)
    show_stock_filter = fields.Boolean('Show Stock Filter in Shop Page', default=True)

    # See All
    see_all = fields.Boolean('See All', default=True)
    show_attr_value = fields.Selection([('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')],
                                       'Total Attributes Value', default='4')

    # B2B Feature
    b2b_hide_add_to_cart = fields.Boolean('Hide Add to Cart Feature')
    b2b_hide_price = fields.Boolean('Hide Product Price')
    is_b2b_message = fields.Boolean('Display Message?')
    text_b2b_hide_details = fields.Char('Text for Details', default='to view price', translate=True)

    # Progressive Web App(PWA)
    is_pwa = fields.Boolean('PWA', readonly=False, help="Enable Progressive Web Application")
    pwa_name = fields.Char(string='Name', readonly=False,
                           help="It will be used in the splash screen and Add To Home Screen’ pop-up.")
    pwa_short_name = fields.Char(string='Short Name', readonly=False,
                                 help="It will be used in a browser pop-up and the app shortcut name.")
    pwa_theme_color = fields.Char(string='Theme Color', readonly=False,
                                  help="The color is used to customize the look of the browser.")
    pwa_bg_color = fields.Char(string='Background Color', readonly=False,
                               help="Splash screen color for home screen shortcut launches.")
    pwa_start_url = fields.Char(string='Start URL', readonly=False,
                                help="URL opened when users tap the app icon on their home screen.")
    app_image_512 = fields.Binary(string='Application Image(512x512)', readonly=False, store=True,
                                  help="Icon for app launcher, home screen, and splash screen. Required dimensions: 512×512.")

    # Sort by: Top sold
    top_sold_duration_days = fields.Integer(string='Top Sold Products Duration (in days)', default=30, )

    # Voice Search
    enable_voice_search = fields.Boolean(string="Enable Voice Search", default=False,
                                         help="Turn on to let customers search products via voice commands.")

    # Sales and visitor count
    enable_sales_visitor_count = fields.Boolean(string="Show Sales and Visitor Count", default=False,
                                                help="Turn on to show sales and visitor counts on product pages.")
    fake_real_sales_count = fields.Integer(string="Fake Sales Count", default=0,
                                           help="Set a number to be added to the actual sales count for display.")
    fake_real_visitor_count = fields.Integer(string="Fake Visitor Count", default=0,
                                             help="Set a number to be added to the actual visitor count for display.")

    # Trending Categories in Search Bar
    enable_search_categ = fields.Boolean(
        string="Trending Categories for Search", default=True,
        help="Enable it to display the trending list in search bar.")
    search_categ_id = fields.Many2many('product.public.category', string='Website Product Category')
    search_placeholder_items = fields.Text(
        string="Search Placeholder Items",
        help="One item per line. These values rotate in the search bar placeholder.",
        translate=True,
    )

    # Age Verification
    enable_age_verification = fields.Boolean(string="Enable Age Verification", default=False,
                                             help="Enable to popup visitors to verify their age before accessing the website.")
    age_verification_message = fields.Html(string="Age Verification Message",
                                           default="You must be at least {age} years old to enter this site.",
                                           help="Set the message for the age verification popup. Include {age} to display the required age.")
    age_verification_warning = fields.Html(string="Age Verification Warning Message",
                                           default="You must be at least {age} years old to access this site.",
                                           help="Set the access-denied warning message. Include {age} to display the required age.")
    background_image_age_verification = fields.Binary(string="Background Image for Age Verification",
                                                      help="Upload a background image for the age verification popup.")
    background_color_age_verification = fields.Char(string="Background Color for Age Verification",
                                                    help="Select a background color for the age verification popup.")
    yes_button_color = fields.Char(string="Yes Button Color",
                                   help="Select the color for the 'Yes' button in the age verification popup.")
    yes_button_text_color = fields.Char(string="Yes Button Text Color",
                                        help="Choose a color for the 'Yes' button text on the age verification popup.")
    no_button_color = fields.Char(string="No Button Color",
                                  help="Choose a color for the 'No' button on the age verification popup.")
    no_button_text_color = fields.Char(string="No Button Text Color",
                                       help="Choose a text color for the 'No' button on the age verification popup.")

    # One-Step Checkout
    enable_one_page_checkout = fields.Boolean(string="Enable One Step Checkout", default=False,
                                              help="Turn on to provide a one-page checkout for a faster, simplified purchase experience.")

    def _search_with_fuzzy(self, search_type, search, limit, order, options):
        curr_website = self.env['website'].get_current_website()
        search_synonyms = False
        count, results, fuzzy_term = 0, [], False
        if search and curr_website.enable_smart_search:
            synonym_groups = self.env['synonym.group'].sudo().search([('website_id', 'in', [curr_website.id, False])])
            if synonym_groups:
                for synonym_group in synonym_groups:
                    synonyms = [synm.strip().lower() for synm in synonym_group.name.split(',')]
                    if search.strip().lower() in synonyms:
                        search_synonyms = synonyms
                        break
            if search_synonyms:
                for search in search_synonyms:
                    fuzzy_term = False
                    search_details = self._search_get_details(search_type, order, options)
                    if search and options.get('allowFuzzy', True):
                        fuzzy_term = self._search_find_fuzzy_term(search_details, search)
                        if fuzzy_term:
                            new_count, new_results = self._search_exact(search_details, fuzzy_term, limit, order)
                            if fuzzy_term.lower() == search.lower():
                                fuzzy_term = False
                        else:
                            new_count, new_results = self._search_exact(search_details, search, limit, order)
                    else:
                        new_count, new_results = self._search_exact(search_details, search, limit, order)

                    for new_res in new_results:
                        if new_res not in results:
                            res = [res for res in results if res['model'] == new_res['model']]
                            if res:
                                for prod in new_res['results']:
                                    if prod not in res[0]['results']:
                                        res[0]['results'] += prod
                                        res[0]['count'] += 1
                                        count += 1
                            else:
                                results.append(new_res)
                                count += new_res['count']
            else:
                count, results, fuzzy_term = super()._search_with_fuzzy(search_type, search, limit,
                                                                        order, options)
        else:
            count, results, fuzzy_term = super()._search_with_fuzzy(search_type, search, limit,
                                                                    order, options)
        return count, results, fuzzy_term

    @staticmethod
    def _get_product_sort_mapping_ept():
        """ Add new sorting option for products based on discount
        Added by: Shubham Kumar
        Date: 6 Oct 2025
        :return: list of tuples
        """
        return [('discount asc', _('Discount')), ("top_sold", _("Top Sold"))]

    def get_all_product_brand_template_filter(self):
        return self.env.ref('emipro_theme_base.dynamic_snippet_filter_product_brand').id

    @api.onchange('is_load_more')
    def _onchange_icon_load_more(self):
        if self.is_load_more:
            img_path = tools.misc.file_path('emipro_theme_base/static/src/img/loadmore.gif')
            with tools.misc.file_open(img_path, 'rb') as f:
                self.load_more_image = base64.b64encode(f.read())

    @api.onchange('is_lazy_load')
    def _onchange_icon_lazy_load(self):
        if self.is_lazy_load:
            img_path = tools.misc.file_path('emipro_theme_base/static/src/img/lazyload.gif')
            with tools.misc.file_open(img_path, 'rb') as f:
                self.lazy_load_image = base64.b64encode(f.read())

    @api.model
    def pager(self, url, total, page=1, step=30, scope=5, url_args=None):
        if 'brand' in url_args:
            url = "/shop/brands/%s" % request.env['ir.http']._slug(url_args['brand'])

        if 'brand' in url_args:
            url_args.pop('brand')

        res = super().pager(url=url, total=total, page=page, step=step, scope=scope, url_args=url_args)

        return res

    @api.onchange('display_out_of_stock')
    def _onchange_display_out_of_stock(self):
        if not self.display_out_of_stock:
            self.show_stock_filter = False
            self.option_out_of_stock = False

    @api.onchange('b2b_hide_price')
    def _onchange_b2b_hide_price(self):
        if self.b2b_hide_price:
            self.b2b_hide_add_to_cart = True

    @api.constrains('b2b_hide_price', 'b2b_hide_add_to_cart', 'is_b2b_message')
    def _check_b2b_message(self):
        for rec in self:
            if rec.is_b2b_message and not (rec.b2b_hide_price or rec.b2b_hide_add_to_cart):
                raise ValidationError(
                    _('You cannot enable “Display Message?” unless “Hide Add to Cart” or “Hide Product Price” is activated.'))

    def display_add_to_cart(self):
        check_hide_add_to_cart = False if self.is_public_user() and self.b2b_hide_add_to_cart else True
        return check_hide_add_to_cart

    def display_product_price(self):
        check_hide_price = False if self.is_public_user() and self.b2b_hide_price else True
        return check_hide_price

    def display_b2b_message(self):
        display_message = True if self.is_public_user() and self.is_b2b_message else False
        return display_message

    def get_remove_url(self, url, option, values):
        vals = {}
        shop_url = url

        request_args = request.httprequest.args
        attribute_values = request_args.getlist('attribute_values')
        attribute_value_pairs = [value.split('-') for value in attribute_values if value]
        attribute_value_dict = {int(pair[0]): [int(value_id) for value_id in pair[1].split(',')] for pair in
                                attribute_value_pairs}

        if option == 'attribute':
            attribute_dict = {}
            attribute_obj = self.env['product.attribute'].sudo()
            attribute_value_obj = self.env['product.attribute.value'].sudo()

            for key, value_list in attribute_value_dict.items():
                for value in value_list:
                    if key != 0:
                        attribute_id = attribute_obj.browse(key)
                        attribute_value = attribute_value_obj.browse(value)
                        option_value = '%s-%s' % (key, value)
                        attr_url = shop_url.replace(f"attribute_values={option_value}", '')
                        if attribute_id not in attribute_dict:
                            attribute_dict[attribute_id] = []
                        attribute_dict[attribute_id].append({attribute_value: attr_url})

            vals.update(attribute_details=attribute_dict)

        if option == 'tag':
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            tags_values = query_params.get('tags', [])
            tag_details = []
            if tags_values:
                tag_obj = self.env['product.tag'].sudo()
                tag_result = [int(x) for x in tags_values[0].split(',')]
                for value in tag_result:
                    current_url = shop_url
                    tag_url = current_url.replace(f"tags={value}", "")
                    tag_id = tag_obj.browse(int(value))
                    tag_details.append({tag_id: tag_url})
            vals.update(tag_details=tag_details)

        if option == 'ratings':
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            ratings_values = query_params.get('rating', [])
            ratings_details = []
            for value in ratings_values:
                current_url = shop_url
                tag_url = current_url.replace(f"rating={value}", "")
                ratings_details.append({value: tag_url})
            vals.update(ratings_details=ratings_details)

        if option == 'brand' and values:
            brand_details = []
            brand_obj = self.env['product.brand'].sudo()
            attribute_value_pairs = [value.split('-') for value in values if value]
            pair = {int(pair[0]): [int(value_id) for value_id in pair[1].split(',')] for pair in attribute_value_pairs}
            for key,value in pair.items():
                if key == 0:
                    for val in value:
                        brand_id = brand_obj.browse(val)
                        option_value = '%s-%s' % (key, val)
                        brand_url = shop_url.replace(f"attribute_values={option_value}", '')
                        brand_details.append({brand_id: brand_url})
            vals.update(brand_filter_details=brand_details)
        return vals

    def list_providers_ept(self):
        """
            This method is used for return the encoded url for the auth providers
            :return: link for the auth providers.
            Added by: Ashvin Rathod
            Date: 24 NOV 2025
        """
        try:
            providers = request.env['auth.oauth.provider'].sudo().search_read([('enabled', '=', True)])
        except Exception:
            providers = []
        for provider in providers:
            return_url = request.httprequest.url_root + 'auth_oauth/signin'
            state = OAuthLogin.get_state(self, provider)
            params = {'response_type': 'token', 'client_id': provider['client_id'], 'redirect_uri': return_url,
                      'scope': provider['scope'], 'state': json.dumps(state)}
            provider['auth_link'] = "%s?%s" % (provider['auth_endpoint'], werkzeug.urls.url_encode(params))
        return providers
