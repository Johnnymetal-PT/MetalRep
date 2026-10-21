# -*- coding: utf-8 -*-

from odoo.http import request, route
from odoo.addons.website_sale.controllers.main import WebsiteSale

class AsProductRecommanded(WebsiteSale):

    @route('/fetch_ai_recommanded_product/<model("product.template"):product>', auth='public', type='jsonrpc', website=True)
    def ai_rmp(self, product):
        """ This method is used to fetch the AI recommended products. """
        is_product_rmp_active = request.env['ir.config_parameter'].sudo().get_param('atharva_theme_base.allow_product_page')
        shop_template = request.env['ir.ui.view'].sudo()._render_template('theme_alan.ai_recommanded_shop_tmpl',{
            'product': product
        })
        product_template = request.env['ir.ui.view'].sudo()._render_template('theme_alan.ai_recommanded_product_tmpl',{
            'product': product
        })

        return {'shop_template': shop_template,'product_template': product_template if is_product_rmp_active else False}

    @route()
    def product(self, product, category=None, pricelist=None, **kwargs):
        """ This method is used to display the product page. """
        res = super(AsProductRecommanded, self).product(product, category=category, pricelist=pricelist, **kwargs)
        is_trigger_active = request.env['ir.config_parameter'].sudo().get_param('theme_alan.trigger_on_product_page')
        is_shop_rmp_active = request.env['ir.config_parameter'].sudo().get_param('theme_alan.allow_shop_page')
        if not request.env.user._is_public() and is_trigger_active and is_shop_rmp_active:
            domain = [('create_uid','=',request.env.user.id),('name','=',product.id)]
            product_touch_id = request.env['product.touch'].search(domain)
            if product_touch_id:
                if product_touch_id.recent_action != 'view':
                    product_touch_id.recent_action = 'view'
            else:
                request.env['product.touch'].create({
                    'name': product.id,
                    'recent_action': 'view',
                })
        show_rmp = request.env['ir.config_parameter'].sudo().get_param('theme_alan.allow_product_page')
        res.qcontext.update({'show_rmp':show_rmp})
        return res
