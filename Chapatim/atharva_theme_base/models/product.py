# -*- coding: utf-8 -*-

import ast
import hashlib
import calendar
from datetime import timedelta

from odoo import models, fields, api
from odoo.tools.translate import html_translate
from odoo.fields import Domain

from odoo.http import request
from odoo.tools import lazy

class ProductTemplate(models.Model):
    """
    Extension of product.template model to support:
      - Hover image for product cards
      - Brand
      - Custom product labels
      - Extra description tab (HTML)
      - Additional product tabs (e.g., Specs, Guides)
      - Product documents section with toggle
      - Related FAQs
      - Auto-detection of color attribute
      - Variant color images storage
      - Computed product rating
    """
    _inherit = 'product.template'

    hover_image = fields.Image('Hover Image', max_width=512, max_height=512)
    product_brand_id = fields.Many2one('as.product.brand', string='Brand', help='Select a brand for this product')
    pro_label_line_ids = fields.One2many('as.product_label.line', 'product_tmpl_id',string='Product Labels', help='Set the product labels')
    product_tab_description = fields.Html(string='Description Tab', translate=html_translate, sanitize_overridable=True, sanitize_attributes=False, sanitize_form=False,)
    pro_tab_ids = fields.One2many('as.product.tab', 'product_id', string='Product Tabs', help='Set the product tabs')
    doc_name = fields.Char(string='Document Name', default='Documents', required=True, translate=True)
    is_active_doc = fields.Boolean(default=False, string='Show Document')
    doc_attachments = fields.Many2many('ir.attachment', string='Product Documents', bypass_search_access=True)
    product_faqs_ids = fields.Many2many('product.faqs', string='Product FAQs')
    have_color_attribute = fields.Boolean(string='Color Attribute', default=False, compute='is_contains_color_attribute', store=True)
    variant_color_images = fields.Char()
    product_rating = fields.Float(string='Product Rating', compute='_compute_product_rating', store=True)

    def _sync_hover_image(self):
        ProductImage = self.env['product.image']

        for product in self:
            if not product.hover_image:
                continue
            hover_img = ProductImage.search([
                ('product_tmpl_id', '=', product.id),
                ('name', '=', 'Hover Image'),
            ], limit=1)

            if hover_img:
                try:
                    hover_img.sudo().write({'image_1920': product.hover_image, 'sequence': 0})
                except Exception:
                    try:
                        hover_img.image_1920 = product.hover_image
                    except Exception:
                        pass
            else:
                hover_img = ProductImage.sudo().create({
                    'name': 'Hover Image',
                    'product_tmpl_id': product.id,
                    'image_1920': product.hover_image,
                    'sequence': 0,
                })

    @api.model_create_multi
    def create(self, vals_lst):
        for vals in vals_lst:
            if vals.get('doc_attachments'):
                doc_list = [i[1] for i in vals['doc_attachments']]
                attachments = self.env['ir.attachment'].sudo().browse(doc_list)
                for record in attachments:
                    if record.id in doc_list:
                        if record.public == False:
                            record.public = True
        records = super(ProductTemplate, self).create(vals_lst)

        for vals, record in zip(vals_lst, records):
            if vals.get('hover_image'):
                try:
                    record._sync_hover_image()
                except Exception:
                    pass

        return records

    def write(self, vals):
        if vals.get('doc_attachments'):
            doc_list = [i[1] for i in vals['doc_attachments']]
            attachments = self.env['ir.attachment'].sudo().browse(doc_list)
            for record in attachments:
                if record.id in doc_list:
                    if record.public == False:
                        record.public = True

        res = super(ProductTemplate, self).write(vals)
        if 'hover_image' in vals:
            for rec in self:
                try:
                    rec._sync_hover_image()
                except Exception:
                    pass

        return res

    def get_variant_color_images(self):
        self.ensure_one()
        if self.variant_color_images:
            return ast.literal_eval(self.variant_color_images)
        else:
            return []

    @api.depends('attribute_line_ids', 'attribute_line_ids.value_ids')
    def is_contains_color_attribute(self):
        for product in self:
            for ptal in product.valid_product_template_attribute_line_ids:
                if ptal.attribute_id.display_type == 'color':
                    product.have_color_attribute = True
                    break
                else:
                    product.have_color_attribute = False


    def _get_combination_info(self, combination=False, product_id=False, add_qty=1, uom_id=False, only_template=False):
        res = super(ProductTemplate, self)._get_combination_info(combination, product_id, add_qty, uom_id, only_template)
        if res.get('has_discounted_price', False):
            per = 100 - ((res['price'] /  res['list_price']) * 100)
            res.update({'as_offer_discount': '{:.2f}'.format(per)})
        return res

    @api.model
    def _search_build_domain(self, domain_list, search, fields, extra=None):
        res = super(ProductTemplate, self)._search_build_domain(domain_list, search, fields, extra)
        new_domain = [res]
        if self.env.context.get('brands',[]) != []:
            new_domain.append([('product_brand_id', 'in', [int(b) for b in self.env.context['brands']])])
        if self.env.context.get('ratings',[]) != []:
            new_domain.append([('rating_avg', '>=', max([int(b) for b in self.env.context['ratings']]))])
        res = Domain.AND(new_domain)
        return res


    @api.depends('message_ids')
    def _compute_product_rating(self):
        ''' Compute product rating '''
        for i in self:
            prodRating = round(i.sudo().rating_get_stats().get('avg') / 1 * 100) / 100
            i.product_rating = prodRating

    def _get_best_seller_product(self, from_date, website_id, limit ):
        """
        Fetch the best-selling products within a given date range for a specific website.

        Args:
            from_date (int): Number of days to look back from today (used to calculate the start date).
            website_id (int): Website ID to filter products (if None, fetch global + website-specific).
            limit (int): Maximum number of products to return.

        Returns:
            list (recordset of product.template):
                List of best-selling products ordered by quantity sold (highest first).
                Only includes published products that are available for sale.
        """

        self.env.cr.execute("""SELECT PT.id, SUM(SO.product_uom_qty),PT.website_id
            FROM sale_order S
            JOIN sale_order_line SO ON (S.id = SO.order_id)
            JOIN product_product P ON (SO.product_id = P.id)
            JOIN product_template pt ON (P.product_tmpl_id = PT.id)
            WHERE S.state in ('sale','done')
            AND (S.date_order >= %s AND S.date_order <= %s)
            AND (PT.website_id IS NULL OR PT.website_id = %s)
            AND PT.active='t'
            AND PT.is_published='t'
            GROUP BY PT.id
            ORDER BY SUM(SO.product_uom_qty)
            DESC LIMIT %s
        """, [fields.Datetime.today() - timedelta(from_date), fields.Datetime.today(), website_id, limit])

        table = self.env.cr.fetchall()
        product_ids = [record[0] for record in table if record[0]]
        # Batch browse and filter once
        products = self.env['product.template'].sudo().browse(product_ids).filtered(
            lambda p: p.sale_ok and p.is_published
        )
        return products

    def _get_on_sale_products(self, website_id, limit=10):
        website = request.website
        pricelist = lazy(website._get_and_cache_current_pricelist)

        PricelistItem = request.env['product.pricelist.item']

        items = PricelistItem.search([
            ('pricelist_id', '=', pricelist.id),
            ('compute_price', 'in', ['fixed', 'percentage']),
            ('applied_on', 'in', ['1_product', '2_product_category', '3_global']),
        ])

        products = request.env['product.template']

        for item in items:
            if item.applied_on == '1_product' and item.product_tmpl_id:
                products |= item.product_tmpl_id

            elif item.applied_on == '2_product_category' and item.categ_id:
                products |= request.env['product.template'].search([
                    ('categ_id', 'child_of', item.categ_id.id),
                    ('website_published', '=', True),
                    ('sale_ok', '=', True),
                ])

            elif item.applied_on == '3_global':
                products |= request.env['product.template'].search([
                    ('website_published', '=', True),
                    ('sale_ok', '=', True),
                ])

            if limit and len(products) >= limit:
                break
        return products[:limit]



class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.template.attribute.value'

    pv_thumbnail = fields.Image(string='Shop Variant Image')

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            image_url = []
            if rec.attribute_id.display_type == 'color':
                domain = [('attribute_id','=',rec.attribute_id.id), ('product_tmpl_id','=',rec.product_tmpl_id.id)]
                attr_lines_ids = self.sudo().search(domain)
                if attr_lines_ids:
                    for attr in attr_lines_ids:
                        if attr.pv_thumbnail:
                            sha = hashlib.sha512(str(attr.write_date).encode('utf-8')).hexdigest()[:7]
                            url = '/web/image/%s/%s/%s%s?unique=%s' % (self._name, attr.id, 'pv_thumbnail', '', sha)
                            image_url.append(url)
                rec.product_tmpl_id.variant_color_images = image_url
        return res

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def get_product_sale_count(self):
            """Return the number of units sold for this product in the configured time range."""
            self.ensure_one()
            if not self.id:
                return 0

            params = self.env['ir.config_parameter'].sudo()
            time_range = params.get_param(
                'atharva_theme_base.product_sales_count_time_range',
                default='last_month'
            )

            today = fields.Datetime.now()
            start_date = end_date = None

            # ================== Compute date range ==================
            if time_range == 'yesterday':
                start_date = (today - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = (today - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)

            elif time_range == 'this_week':
                start_date = (today - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = today

            elif time_range == 'last_week':
                last_sunday = (today - timedelta(days=today.weekday() + 1)).replace(hour=23, minute=59, second=59, microsecond=999999)
                start_date = (last_sunday - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = last_sunday

            elif time_range == 'this_month':
                start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = today

            else:  # last_month or fallback
                first_day_this_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                last_day_last_month = first_day_this_month - timedelta(days=1)
                start_date = last_day_last_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = last_day_last_month.replace(hour=23, minute=59, second=59, microsecond=999999)

            # ================== Build domain ==================
            website_id = self.env['website'].get_current_website().id
            domain = [
                ('state', '=', 'sale'),
                ('product_id', '=', self.id),
                ('date', '>=', start_date),
                ('date', '<=', end_date),
                ('website_id', 'in', [website_id, False]),
            ]

            result = self.env['sale.report']._read_group(
                domain,
                aggregates=['product_uom_qty:sum'],
                groupby=['product_id'],
            )

            qty = 0
            if result:
                for rec, total in result:
                    if rec and rec.id == self.id:
                        qty = total or 0
                        break

            return int(qty)

    def _get_offer_timing(self):

        pricelist = lazy(request.website._get_and_cache_current_pricelist)
        common_domain = [('date_end', '!=', False), ('show_timer', '=', True)]
        checks = [
            ('0_product_variant', {'product_id': self.id}),
            ('1_product', {'product_tmpl_id': self.product_tmpl_id.id}),
            ('2_product_category', {'categ_id': self.categ_id.id}),
            ('3_global', {}),
        ]
        for applied_on, extra_domain in checks:
            domain = [('id', 'in', pricelist.item_ids.mapped('id')), ('applied_on', '=', applied_on)] + common_domain
            for k, v in extra_domain.items():
                domain.append((k, '=', v))
            item = pricelist.item_ids.search(domain, limit=1)
            if item and item.date_start and (fields.Datetime.today() >= item.date_start):
                return {
                    'date_end': item.date_end,
                    'date_start': item.date_start,
                    'pricelist_item_id': item.id,
                    'applied_on': applied_on,
                }
        return False

    def _get_current_viewers(self):
        self.ensure_one()

        online_after = fields.Datetime.now() - timedelta(minutes=5)

        tracks = self.env['website.track'].sudo().search([
            ('product_id', '=', self.id),
            ('visitor_id.last_connection_datetime', '>=', online_after),
        ])

        return len(set(tracks.mapped('visitor_id').ids))


    def _get_best_seller_product(self, from_date, website_id, limit ):
        self.env.cr.execute("""
            SELECT P.id, SUM(SO.product_uom_qty)
            FROM sale_order S
            JOIN sale_order_line SO ON S.id = SO.order_id
            JOIN product_product P ON SO.product_id = P.id
             JOIN product_template pt ON (P.product_tmpl_id = PT.id)
            WHERE S.state IN ('sale', 'done')
            AND S.date_order BETWEEN %s AND %s
            AND (PT.website_id IS NULL OR PT.website_id = %s)
            AND PT.active = 't'
            AND PT.is_published = 't'
            GROUP BY P.id
            ORDER BY SUM(SO.product_uom_qty) DESC
            LIMIT %s
        """, [
            fields.Datetime.today() - timedelta(from_date),
            fields.Datetime.today(),
            website_id,
            limit
        ])

        table = self.env.cr.fetchall()
        products = []
        for record in table:
            if record[0]:
                variant = self.env['product.product'].sudo().browse(record[0])
                if variant.product_tmpl_id.sale_ok and variant.product_tmpl_id.is_published:
                    products.append(variant)
        return products

    def _to_markup_data(self, website):
        res = super(ProductProduct, self)._to_markup_data(website)
        if getattr(website, 'active_b2b_mode', False) and self.env.user._is_public():
            res.pop('offers', None)
        return res
