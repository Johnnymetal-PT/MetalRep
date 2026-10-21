# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields,SUPERUSER_ID, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.http import request

class res_partner(models.Model):
    _inherit = "res.partner"
    
    product_ids = fields.Many2many('product.template',string='Products')
    product_categ_ids = fields.Many2many('product.category','categ_id','res_partner_categ_id','product_category',string="Product Category") 
    product_variant_ids = fields.Many2many('product.product', 'product_product_id','res_partner_variant_id','product_partner_variant_res',string='Product Variants')

class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.template.attribute.value'
    
    attr_active = fields.Boolean("Attribute Active")

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    product_attr_active = fields.Boolean("Attribute Active")

class Company(models.Model):
    _inherit = 'res.company'

    is_website_product_visibility = fields.Boolean(
        string='Is product visibility'
    )

    visitor_product_ids = fields.Many2many('product.template', 'vstr_prod_tem_id',
        'vstr_partner_id','product_vstr_res',string='Products')

    visitor_product_categ_ids = fields.Many2many('product.category','vstr_categ_id',
        'vstr_part_categ_id','vstr_product_category',string="Product Category")

    visitor_product_variant_ids = fields.Many2many('product.product', 'vstr_product_product_id',
        'vstr_res_partner_variant_id','vstr_product_partner_variant_res',string='Product Variants')

class website(models.Model):
    _inherit = 'website'

    is_website_product_visibility = fields.Boolean(
        string='Is product visibility', related="company_id.is_website_product_visibility", readonly=False
    )

    visitor_product_ids = fields.Many2many('product.template', 'vstr_prod_tem_id',
        'vstr_partner_id','product_vstr_res',string='Products',
        related="company_id.visitor_product_ids",readonly=False)

    visitor_product_categ_ids = fields.Many2many('product.category','vstr_categ_id',
        'vstr_part_categ_id','vstr_product_category',string="Product Category",
        related="company_id.visitor_product_categ_ids",readonly=False)

    visitor_product_variant_ids = fields.Many2many('product.product', 'vstr_product_product_id',
        'vstr_res_partner_variant_id','vstr_product_partner_variant_res',string='Product Variants',
        related="company_id.visitor_product_variant_ids",readonly=False)   

    def get_hidden_public_category_names(self):
        partner = self.env.user.partner_id
        if self.env.user._is_public():
            hidden_categs = self.visitor_product_categ_ids
        else:
            hidden_categs = partner.product_categ_ids
        return hidden_categs.mapped('name') if self.is_website_product_visibility else []
    
    def sale_product_domain(self):
        res = super(website, self).sale_product_domain()
        if not self.is_website_product_visibility :
            return res
        all_attributes = self.env['product.template.attribute.value'].sudo().search([])
        for attrs in all_attributes:
            attrs.sudo().write({'attr_active':False})
        all_products = self.env['product.template'].sudo().search([])
        for products in all_products:
            products.sudo().write({'product_attr_active':False})
        website_domain = self.get_current_website().website_domain()
        product_template_ids = []
        is_public = self.env.user._is_public()
        if is_public:
            if self.visitor_product_ids :
                product_template_ids.extend(self.visitor_product_ids.ids)
                for template in self.visitor_product_ids:
                    template.sudo().write({'product_attr_active':True})
            if self.visitor_product_categ_ids :
                categ_prods = self.env['product.template'].sudo().search([('categ_id','in',self.visitor_product_categ_ids.ids)])
                if categ_prods :
                    product_template_ids.extend(categ_prods.ids)
                for template in categ_prods:
                    template.sudo().write({'product_attr_active':True})
            if self.visitor_product_variant_ids :
                product_product = self.env['product.product'].sudo().search([('id','in',self.visitor_product_variant_ids.ids)])
                attr_prods = self.env['product.template'].sudo().search([('product_variant_ids','in',product_product.ids)])
                if attr_prods :
                    product_template_ids.extend(attr_prods.ids)
                    for product_attrs in product_product.product_template_attribute_value_ids:
                        product_attrs.sudo().write({'attr_active':True})
        else:
            parnter = self.env.user.partner_id
            if parnter.product_ids :
                product_template_ids.extend(parnter.product_ids.ids)
                for template in parnter.product_ids:
                    template.sudo().write({'product_attr_active':True})
            if parnter.product_categ_ids :
                categ_prods = self.env['product.template'].sudo().search([('categ_id','in',parnter.product_categ_ids.ids)])
                if categ_prods :
                    product_template_ids.extend(categ_prods.ids)
                for template in categ_prods:
                    template.sudo().write({'product_attr_active':True})
            if parnter.product_variant_ids:
                product_product = self.env['product.product'].sudo().search([('id','in',parnter.product_variant_ids.ids)])
                attr_prods = self.env['product.template'].sudo().search([('product_variant_ids','in',product_product.ids)])
                if attr_prods :
                    product_template_ids.extend(attr_prods.ids)
                    for product_attrs in product_product.product_template_attribute_value_ids:
                        product_attrs.sudo().write({'attr_active':True})

        return ['&'] + res + [('id', 'in', product_template_ids)]



class visitor_product(models.TransientModel):
    _inherit = 'res.config.settings'

    is_website_product_visibility = fields.Boolean(
        string='Is product visibility', related="company_id.is_website_product_visibility", readonly=False
    )

    visitor_product_ids = fields.Many2many('product.template', 'vstr_prod_tem_id',
        'vstr_partner_id','product_vstr_res',string='Products',
        related="company_id.visitor_product_ids",readonly=False)

    visitor_product_categ_ids = fields.Many2many('product.category','vstr_categ_id',
        'vstr_part_categ_id','vstr_product_category',string="Product Category",
        related="company_id.visitor_product_categ_ids",readonly=False)

    visitor_product_variant_ids = fields.Many2many('product.product', 'vstr_product_product_id',
        'vstr_res_partner_variant_id','vstr_product_partner_variant_res',string='Product Variants',
        related="company_id.visitor_product_variant_ids",readonly=False)
