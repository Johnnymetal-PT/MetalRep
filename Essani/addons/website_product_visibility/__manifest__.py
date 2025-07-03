# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    "name" : "Website Product Visibility Odoo",
    "version" : "18.0.0.0",
    "description": """
        This module use for
Website Product Visibility by customer
Website Product Visibility by partner
Website Product Visibility by product catergory
Website Product Visibility by category
Website Product Visibility for customer
Website Product Visibility for category
Website Product Visibility for partner

webshop Product Visibility by customer
webshop Product Visibility by partner
webshop Product Visibility by product catergory
webshop Product Visibility by category
webshop Product Visibility for customer
webshop Product Visibility for category
webshop Product Visibility for partner

Website Product Visibility website
webstore Product Visibility webstore
website item visibility website
Website Shop Product Visibility website
webshop Product Visibility webshop
website product visible on store
website visible product on store
website visible item on store
website make filter on product for webshop 
website product filter website
website product category filter website
website Allowed Product for Partner Allowed category for partner Allow product on shop for customer Hide product for customer
website visible product on shop Visible product on website Website product hide on website

webshop item visibility webshop
web Shop Product Visibility webshop
webshop product visible on webshop
webshop visible product on webshop
webshop visible item on webshop
webshop make filter on product for website 
webshop product filter webshop
webshop product category filter webshop
webshop Allowed Product for Partner webshop Allowed category for partner webshop Allow product on webshop for customer Hide product for customer
webshop visible product on shop Visible product on webshop product hide on website

webstore item visibility webstore
webstore Product Visibility webstore
webstore product visible on webstore
webstore visible product on webstore
webstore visible item on webstore
webstore make filter on product for webstore 
webstore product filter webstore
webstore product category filter webstore
webstore Allowed Product for Partner webstore Allowed category for partner webstore Allow product on webstore for customer Hide product for customer
webstore visible product on shop Visible product on webstore product hide on webstore

eCommerce item visibility eCommerce
eCommerce Product Visibility eCommerce
eCommerce product visible on eCommerce
eCommerce visible product on eCommerce
eCommerce visible item on eCommerce
eCommerce make filter on product for eCommerce 
eCommerce product filter eCommerce
eCommerce product category filter eCommerce
eCommerce Allowed Product for Partner eCommerce Allowed category for partner eCommerce Allow product on eCommerce for customer Hide product for customer
eCommerce visible product on shop Visible product on eCommerce product hide on eCommerce

e-Commerce item visibility e-Commerce
e-Commerce Product Visibility e-Commerce
e-Commerce product visible on e-Commerce
e-Commerce visible product on e-Commerce
e-Commerce visible item on e-Commerce
e-Commerce make filter on product for e-Commerce 
e-Commerce product filter e-Commerce
e-Commerce product category filter e-Commerce
e-Commerce Allowed Product for Partner e-Commerce Allowed category for partner e-Commerce Allow product on e-Commerce for customer Hide product for customer
e-Commerce visible product on shop Visible product on e-Commerce product hide on e-Commerce

e Commerce item visibility e Commerce
e Commerce Product Visibility e Commerce
e Commerce product visible on e Commerce
e Commerce visible product on e Commerce
e Commerce visible item on e Commerce
e Commerce make filter on product for e Commerce 
e Commerce product filter e Commerce
e Commerce product category filter e Commerce
e Commerce Allowed Product for Partner e Commerce Allowed category for partner e Commerce Allow product on e Commerce for customer Hide product for customer
e Commerce visible product on shop Visible product on e Commerce product hide on e Commerce

Website Product Visibility for website users and Visitors
Website Product Visibility for login users and Visitors
webshop Product Visibility for website users and Visitors
webshop Product Visibility for login users and Visitors
It allows to set product visibility based on customer on website
User can allow to add products/product category which going to be display for webshop for specific customer.
    """,
    "category" : "eCommerce",
    "depends" : ['base','sale_management','website_sale'],
    "author": "BROWSEINFO",
    'summary': 'Apps visible hide product on shop based on Customer Country Specific Product Visibility by User Role hidden products Catalog Visibility Price Visibility Hide Product from Customers Restrict Products item visibility website products visibility filter portal',
    'website':"https://www.browseinfo.com/demo-request?app=website_product_visibility&version=18&edition=Community",
    "data": [
        'views/res_partner_view.xml',
        'views/product_visibility_template.xml',
    ],
    'qweb': [],
    "price": 15,
    "currency": 'EUR',
    "auto_install": False,
    "installable": True,
    "license": "OPL-1",
    'live_test_url':'https://www.browseinfo.com/demo-request?app=website_product_visibility&version=18&edition=Community',
    "images":['static/description/Banner.gif'],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

