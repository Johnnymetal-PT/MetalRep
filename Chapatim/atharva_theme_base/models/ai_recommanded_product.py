# -*- coding: utf-8 -*-

import os
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import config

# NOTE: joblib and sklearn imports are lazy-loaded in methods to avoid
# non-idempotent code execution during Odoo upgrades in multi-worker environments

_logger = logging.getLogger(__name__)

def make_recommended_path(env):
    base_path = config.filestore(env.cr.dbname)

    folder_name = 'recommand_product'
    folder_path = os.path.join(base_path, folder_name)

    # Create folder if it doesn't exist
    os.makedirs(folder_path, exist_ok=True)
    file_names = ['system_products.json', 'kmeans_model.pkl', 'nn_model.pkl', 'vectorizer_model.pkl']
    for file_name in file_names:
        file_path = os.path.join(folder_path, file_name)
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                pass

    return folder_path

class ProductWishlistExtend(models.Model):
    _inherit = 'product.wishlist'

    @api.model
    def _add_to_wishlist(self, pricelist_id, currency_id, website_id, price, product_id, partner_id=False):
        res = super(ProductWishlistExtend, self)._add_to_wishlist(
            pricelist_id, currency_id, website_id, price, product_id, partner_id=partner_id
        )
        is_trigger_active = self.env['ir.config_parameter'].sudo().get_param('atharva_theme_base.trigger_on_wishlist')
        is_shop_rmp_active = self.env['ir.config_parameter'].sudo().get_param('atharva_theme_base.allow_shop_page')

        if not self.env.user._is_public() and is_trigger_active and is_shop_rmp_active:
            product = self.env['product.product'].browse(int(product_id)).product_tmpl_id
            domain = [('create_uid','=',self.env.user.id),('name','=',product.id)]
            product_touch_id = self.env['product.touch'].search(domain)
            if product_touch_id:
                if product_touch_id.recent_action != 'wishlist':
                    product_touch_id.recent_action = 'wishlist'
            else:
                self.env['product.touch'].create({
                    'name': product.id,
                    'recent_action': 'wishlist',
                })
        return res

class SaleOrderExtend(models.Model):
    _inherit = 'sale.order'

    def _cart_update(self, product_id, line_id=None, add_qty=0, set_qty=0, **kwargs):
        res = super(SaleOrderExtend, self)._cart_update(product_id, line_id, add_qty, set_qty, **kwargs)
        is_trigger_active = self.env['ir.config_parameter'].sudo().get_param('atharva_theme_base.trigger_on_add_to_cart')
        is_shop_rmp_active = self.env['ir.config_parameter'].sudo().get_param('atharva_theme_base.allow_shop_page')
        if not self.env.user._is_public() and is_trigger_active and is_shop_rmp_active:
            product = self.env['product.product'].browse(int(product_id)).product_tmpl_id
            domain = [('create_uid','=',self.env.user.id),('name','=',product.id)]
            product_touch_id = self.env['product.touch'].search(domain)
            if product_touch_id:
                if product_touch_id.recent_action != 'cart':
                    product_touch_id.recent_action = 'cart'
            else:
                self.env['product.touch'].create({
                    'name': product.id,
                    'recent_action': 'cart',
                })
        return res

    def action_confirm(self):
        res = super(SaleOrderExtend, self).action_confirm()

        is_trigger_active = self.env['ir.config_parameter'].sudo().get_param('atharva_theme_base.trigger_on_confirm_order')
        is_shop_rmp_active = self.env['ir.config_parameter'].sudo().get_param('atharva_theme_base.allow_shop_page')

        if not self.env.user._is_public() and is_trigger_active and is_shop_rmp_active:
            for order in self:
                if order.state == 'sale' and order.website_id:
                    user = self.env['res.users'].search([('partner_id', '=', order.partner_id.id)])
                    if user:
                        for line in order.order_line:
                            product = line.product_id.product_tmpl_id
                            if not line.is_delivery:
                                domain = [('create_uid', '=', user.id), ('name', '=', product.id)]
                                product_touch_id = self.env['product.touch'].search(domain)
                                if product_touch_id:
                                    if product_touch_id.recent_action != 'on_confirm':
                                        product_touch_id.recent_action = 'on_confirm'
                                else:
                                    self.env['product.touch'].with_user(user.id).create({
                                        'name': product.id,
                                        'recent_action': 'on_confirm',
                                    })
        return res


class ProductTouch(models.Model):
    _name = 'product.touch'
    _description = 'Product Touch'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # for tracking and activities

    name = fields.Many2one('product.template', required=True)
    recent_action = fields.Selection([
        ('view', 'View Product'),('cart', 'Add to Cart'),('wishlist', 'Add to Wishlist')
        ,('on_confirm', 'Sale Order Confirm')
    ], string='Recent Action', tracking=True)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _get_stop_words(self):
        """
        Hook to override the stop words for TfidfVectorizer.
        Can be overridden in child classes or modules to use different language stop words.

        Returns:
            str: Language code for stop words (e.g., 'english', 'german', 'french', etc.)
                or a custom list of stop words.
        """
        return 'english'

    def create_product_json_file_data(self):
        recommanded_product_path = make_recommended_path(self.env)
        products = self.env['product.template'].search([])
        model_fields = self.env['ir.config_parameter'].sudo().get_param('atharva_theme_base.rmp_product_field_raw_ids', '[]')

        field_ids = json.loads(model_fields)  # Convert JSON string to list
        dynamic_fields = self.env['ir.model.fields'].browse(field_ids)
        product_data = []
        for product in products:
            product_info = {}
            product_info['id'] = product.id
            for field in dynamic_fields:
                if hasattr(product, field.name):
                    field_value = getattr(product, field.name, '')
                    if field.ttype == 'many2many':
                        product_info[field.name] = ', '.join(field_value.mapped('display_name')) if field_value else ''
                    elif field.ttype == 'many2one':
                        product_info[field.name] = field_value.display_name if field_value.display_name else ''
                    else:
                        product_info[field.name] = field_value if field_value else ''
            product_data.append(product_info)

        file_path = os.path.join(recommanded_product_path, 'system_products.json')
        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(product_data, json_file, ensure_ascii=False, indent=4)

    def pretrain_model_recommandation(self):
        """Pretrain the recommendation models and save them."""
        # Lazy import to avoid loading heavy ML libraries during module upgrade
        if config.get('update_module'):
            _logger.warning('Skipping model pretraining during module upgrade')
            return

        try:
            import joblib
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.neighbors import NearestNeighbors
            from sklearn.cluster import KMeans
        except ImportError as e:
            raise UserError(_('Required ML libraries not available: %s. Please install scikit-learn and joblib.') % str(e))

        # Step 1: Load the JSON data
        recommanded_product_path = make_recommended_path(self.env)
        file_path = os.path.join(recommanded_product_path, 'system_products.json')
        with open(file_path, 'r') as file:
            data = json.load(file)

        model_fields = self.env['ir.config_parameter'].sudo().get_param('atharva_theme_base.rmp_product_field_raw_ids', '[]')
        field_ids = json.loads(model_fields)  # Convert JSON string to list
        field_selection = self.env['ir.model.fields'].browse(field_ids).mapped('name')

        texts = []
        skipped_count = 0

        for item in data:
            # Keep only non-empty field values
            parts = [
                str(item[field]).strip()
                for field in field_selection
                if field in item and str(item[field]).strip()
            ]
            if parts:
                texts.append(' - '.join(parts))
            else:
                skipped_count += 1

        if not texts:
            raise ValidationError( 'No valid text data found for training. ' 'Please check the selected fields or product data.')

        # Step 2: Feature extraction
        stop_words = self._get_stop_words()
        vectorizer = TfidfVectorizer(stop_words=stop_words, max_features=500)
        X = vectorizer.fit_transform(texts)
        # Step 3: Train KMeans clustering model
        num_clusters = 5
        kmeans = KMeans(n_clusters=num_clusters, random_state=42)
        kmeans.fit(X)
        nn = NearestNeighbors(n_neighbors=10, metric='cosine')
        nn.fit(X)
        # Save the models
        kmeans_model_path = os.path.join(recommanded_product_path, 'kmeans_model.pkl')
        joblib.dump(kmeans, kmeans_model_path)
        # Save the Nearest Neighbors model
        nn_model_path = os.path.join(recommanded_product_path, 'nn_model.pkl')
        joblib.dump(nn, nn_model_path)
        # Save the TfidfVectorizer
        vectorizer_model_path = os.path.join(recommanded_product_path, 'vectorizer_model.pkl')
        joblib.dump(vectorizer, vectorizer_model_path)

    def fetch_ai_recommanded_product(self):
        # Lazy import to avoid loading heavy ML libraries during module upgrade
        if config.get('update_module'):
            _logger.warning('Skipping AI product recommendation during module upgrade')
            return self.browse([])
        try:
            import joblib
        except ImportError as e:
            _logger.warning('joblib not available for AI recommendations: %s', str(e))
            return self.browse([])

        recommanded_product_path = make_recommended_path(self.env)
        website = self.env['website'].get_current_website()
        model_fields = self.env['ir.config_parameter'].sudo().get_param('atharva_theme_base.rmp_product_field_raw_ids', '[]')
        field_ids = json.loads(model_fields)
        field_selection = self.env['ir.model.fields'].browse(field_ids)

        validated_distance = self.env['ir.config_parameter'].sudo().get_param('atharva_theme_base.rmp_similar_score', 0.7)

        if len(self) == 0:
            data_product = self.env['product.touch'].search([('create_uid','=', self.env.user.id)])
        else:
            data_product = self
        recommand_product = []
        recommand_product_ids = []

        try:
            """Find similar products based on the pre-trained models."""
            # Ensure models are loaded
            kmeans_model_path = os.path.join(recommanded_product_path, 'kmeans_model.pkl')
            kmeans = joblib.load(kmeans_model_path)

            # Load the Nearest Neighbors model
            nn_model_path = os.path.join(recommanded_product_path, 'nn_model.pkl')
            nn = joblib.load(nn_model_path)

            # Load the TfidfVectorizer
            vectorizer_model_path = os.path.join(recommanded_product_path, 'vectorizer_model.pkl')
            vectorizer = joblib.load(vectorizer_model_path)

            for product in data_product:
                # Vectorize the input product name
                product_info = []
                if len(self) == 0:
                    for field in field_selection:
                        if hasattr(product.name, field.name):
                            field_value = getattr(product.name, field.name, '')
                            if field.ttype == 'many2many':
                                text = ', '.join(field_value.mapped('display_name')) if field_value else ''
                                product_info.append(text)
                            elif field.ttype == 'many2one':
                                text = field_value.display_name if field_value.display_name else ''
                                product_info.append(text)
                            else:
                                text = field_value if field_value else ''
                                product_info.append(text)
                else:
                    for field in field_selection:
                        if hasattr(product, field.name):
                            field_value = getattr(product, field.name, '')
                            if field.ttype == 'many2many':
                                text = ', '.join(field_value.mapped('display_name')) if field_value else ''
                                product_info.append(text)
                            elif field.ttype == 'many2one':
                                text = field_value.display_name if field_value.display_name else ''
                                product_info.append(text)
                            else:
                                text = field_value if field_value else ''
                                product_info.append(text)
                texts = [' - '.join(product_info)]
                input_vector = vectorizer.transform(texts)
                # Find nearest neighbors
                distances, indices = nn.kneighbors(input_vector)

                # Collect similar products
                similar_products = []
                with open(os.path.join(recommanded_product_path, 'system_products.json'), 'r') as file:
                    data = json.load(file)
                    for index, distance in zip(indices[0], distances[0]):
                        if distance <= float(validated_distance):
                            similar_product = data[index]
                            recommand_product_ids.append(similar_product['id'])
                            similar_product.update({'distance': distance})
                            similar_products.append(similar_product)
                recommand_product.append(similar_products)

            if len(self) == 0:
                for pt in data_product:
                    if pt.name.id in recommand_product_ids:
                        recommand_product_ids.remove(pt.name.id)
            else:
                if self.id in recommand_product_ids:
                    recommand_product_ids.remove(self.id)

            # recommand_product_ids = recommand_product_ids[:30]
            # products = self.browse(recommand_product_ids)

            recommand_product_ids = list(set(recommand_product_ids[:30]))
            products = self.browse(recommand_product_ids).filtered(lambda p: p.website_published)
            product_list = []
            for product in products:
                if product.website_id.id in website.ids or product.website_id.id == False:
                    product_list.append(product.id)

            products = self.browse(product_list)
            return products

        except Exception as e:
            _logger.warning(f'\n\nERROR In Recommanded Product: {e}')

class RecommandationConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'
    _description = 'Product Recommendation Configuration'

    rmp_product_field_ids = fields.Many2many(
        'ir.model.fields',
        string='Product Field for Recommendations'
    )
    rmp_product_field_raw_ids = fields.Char(
        string='Product Field for Train Model',
        config_parameter='atharva_theme_base.rmp_product_field_raw_ids'
    )
    rmp_model_and_dataset_location = fields.Char(
        string='Model and Dataset Location',
        config_parameter='atharva_theme_base.model_and_dataset_location'
    )

    rmp_allow_shop_page = fields.Boolean(
        string='Shop Page',
        config_parameter='atharva_theme_base.allow_shop_page'
    )
    rmp_allow_product_page = fields.Boolean(
        string='Product Page',
        config_parameter='atharva_theme_base.allow_product_page'
    )
    rmp_trigger_on_product_page = fields.Boolean(
        string='Visit Product Page',
        config_parameter='atharva_theme_base.trigger_on_product_page'
    )
    rmp_trigger_on_add_to_cart = fields.Boolean(
        string='On Add to Cart',
        config_parameter='atharva_theme_base.trigger_on_add_to_cart'
    )
    rmp_trigger_on_wishlist = fields.Boolean(
        string='On Add to Wishlist',
        config_parameter='atharva_theme_base.trigger_on_wishlist'
    )
    rmp_trigger_on_confirm_order = fields.Boolean(
        string='On Confirm Order',
        config_parameter='atharva_theme_base.trigger_on_confirm_order'
    )
    rmp_similar_score = fields.Float(
        string='Recommanded Product Score',
        config_parameter='atharva_theme_base.rmp_similar_score'
    )

    @api.model
    def get_values(self):
        """Load default values from ir.config_parameter."""
        res = super(RecommandationConfiguration, self).get_values()
        params = self.env['ir.config_parameter'].sudo()

        field_ids = params.get_param('atharva_theme_base.rmp_product_field_raw_ids', default='[]')
        field_ids = json.loads(field_ids)
        if len(field_ids) != 0:
            res.update(
                rmp_product_field_ids=[(6,0,field_ids)]
            )
        res.update(
            rmp_product_field_raw_ids=params.get_param('atharva_theme_base.rmp_product_field_raw_ids', default='[]'),
            rmp_allow_shop_page=bool(params.get_param('atharva_theme_base.allow_shop_page', default=False)),
            rmp_allow_product_page=bool(params.get_param('atharva_theme_base.allow_product_page', default=False)),
            rmp_trigger_on_product_page=bool(params.get_param('atharva_theme_base.trigger_on_product_page', default=False)),
            rmp_trigger_on_add_to_cart=bool(params.get_param('atharva_theme_base.trigger_on_add_to_cart', default=False)),
            rmp_trigger_on_wishlist=bool(params.get_param('atharva_theme_base.trigger_on_wishlist', default=False)),
            rmp_trigger_on_confirm_order=bool(params.get_param('atharva_theme_base.trigger_on_confirm_order', default=False)),
            rmp_similar_score=float(params.get_param('atharva_theme_base.rmp_similar_score', default=0.7)),

        )
        return res

    def set_values(self):
        """Save values into ir.config_parameter."""
        super(RecommandationConfiguration, self).set_values()
        params = self.env['ir.config_parameter'].sudo()

        if self.rmp_allow_shop_page or self.rmp_allow_product_page:
            if len(self.rmp_product_field_ids) == 0:
                raise UserError(_('You need to select at least one field to train the recommended model. Please choose the appropriate field(s) to proceed.'))
            if not (self.rmp_similar_score >= 0.0 and self.rmp_similar_score <= 1.0):
                raise UserError(_('The similarity score must be between 0.0 and 1.0. Please ensure the value is within this range.'))

        params.set_param('atharva_theme_base.rmp_product_field_raw_ids', str(self.rmp_product_field_ids.mapped('id')) or '[]')
        params.set_param('atharva_theme_base.allow_shop_page', self.rmp_allow_shop_page or False)
        params.set_param('atharva_theme_base.allow_product_page', self.rmp_allow_product_page or False)
        params.set_param('atharva_theme_base.trigger_on_product_page', self.rmp_trigger_on_product_page or False)
        params.set_param('atharva_theme_base.trigger_on_add_to_cart', self.rmp_trigger_on_add_to_cart or False)
        params.set_param('atharva_theme_base.trigger_on_wishlist', self.rmp_trigger_on_wishlist or False)
        params.set_param('atharva_theme_base.trigger_on_confirm_order', self.rmp_trigger_on_confirm_order or False)
        params.set_param('atharva_theme_base.rmp_similar_score', self.rmp_similar_score or 0.7)

    def create_product_json_file_data(self):
        self.env['product.template'].create_product_json_file_data()

    def pretrain_model_recommandation(self):
        self.env['product.template'].pretrain_model_recommandation()

    def view_recommandation_trigger(self):
        action = self.env.ref('atharva_theme_base.action_product_touch').read()[0]
        return action
