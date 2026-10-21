# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class PriceListExtend(models.Model):
    _inherit = 'product.pricelist.item'

    show_offers = fields.Boolean(string='Show Future Offers', default=False)
    offer_msg = fields.Char(string='Offer Message', default="Hurry Up! Limited time offer.", required=True)
    offer_alert_msg = fields.Text(string='Offer Days Left',  default="New offer coming in @ days")


class ProductBrand(models.Model):
    _inherit = 'as.product.brand'

    visible_slider = fields.Boolean(string='Visible in Website', default=True)


class ProductTags(models.Model):
    _name = "product.tags"
    _inherit = ['website.searchable.mixin',]
    _description = "Product Tags"
    _order = "sequence, id"

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(default=True, help="The active field allows you to hide the tag without removing it.")
    sequence = fields.Integer(help="Gives the sequence order when displaying a list of rules.")
    product_ids = fields.Many2many('product.template', string='Products')
    website_id = fields.Many2one('website', string='Website')


class ProductTemplateTagExtend(models.Model):
    _inherit = 'product.template'

    product_tags_ids = fields.Many2many('product.tags', string='Product Tags')


class WebsiteExtend(models.Model):
    _inherit = 'website'

    is_alan = fields.Boolean(string="Is theme Alan?", compute="_is_theme_alan", default=False)
    categ_search_active = fields.Boolean(string="Category Search", help='Enable to activate advance category search.')
    attr_search_active = fields.Boolean(string="Attribute Search", help='Enable to activate advance attribute search.')
    brand_search_active = fields.Boolean(string="Brand Search", help='Enable to activate advance brand search.')
    tag_search_active = fields.Boolean(string="Tag Search", help='Enable to activate advance tag search.')
    categories_to_show = fields.Integer(string='Number of Categories', store=True)
    attributes_to_show = fields.Integer(string='Number of Attributes', store=True)
    brands_to_show = fields.Integer(string='Number of Brands', store=True)
    tags_to_show = fields.Integer(string='Number of Tags', store=True)
    is_breadcum = fields.Boolean(string='Do you want to disable Breadcrumb?', default=False)


class QckSearchConfigs(models.TransientModel):
    _inherit = "res.config.settings"

    is_alan = fields.Boolean(string="Is theme Alan", related="website_id.is_alan")
    categ_search_active = fields.Boolean(string='Activate Advance Category Search', related='website_id.categ_search_active', readonly=False, help='Enable to activate advance category search.')
    attr_search_active = fields.Boolean(string='Activate Advance Attribute Search', related='website_id.attr_search_active', readonly=False, help='Enable to activate advance attribute search.')
    brand_search_active = fields.Boolean(string='Activate Advance Brand Search', related='website_id.brand_search_active', readonly=False, help='Enable to activate advance brand search.')
    tag_search_active = fields.Boolean(string='Activate Advance Tag Search', related='website_id.tag_search_active', readonly=False, help='Enable to activate advance tag search.')
    categories_to_show = fields.Integer(string='Number of Categories', related='website_id.categories_to_show', readonly=False)
    attributes_to_show = fields.Integer(string='Number of Attributes', related='website_id.attributes_to_show', readonly=False)
    brands_to_show = fields.Integer(string='Number of Brands', related='website_id.brands_to_show', readonly=False)
    tags_to_show = fields.Integer(string='Number of Tags', related='website_id.tags_to_show', readonly=False)
