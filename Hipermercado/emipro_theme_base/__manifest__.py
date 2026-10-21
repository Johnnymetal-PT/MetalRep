# -*- coding: utf-8 -*-

#######################################################################################
# Emipro Theme Base Module Manifest File.
#
# This file contains the metadata for the Emipro Theme Base module, including:
#     - Module name, version, and category
#     - Summary and description
#     - Author and license information
#     - Dependencies on other modules
#     - Data, demo, and security files to load
#     - Application, install, and auto-install flags
#
# Odoo uses this file to identify, install, and manage the module.
#######################################################################################

{
    # Theme information
    'name': 'Emipro Theme Base',
    'category': 'Base',
    'summary': 'Base module containing common libraries for all Emipro eCommerce themes.',
    'version': '19.0.0.7',
    'license': 'OPL-1',

    'depends': ["website_sale_stock", "website_sale_comparison_wishlist"],

    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/mobile_header_icon.xml',
        'views/website.xml',
        'views/product_pricelist.xml',
        'views/product_template.xml',
        'views/product_tabs.xml',
        'views/synonym_group.xml',
        'views/search_keyword_report.xml',
        'views/website_menu_view.xml',
        'views/menu_label.xml',
        'views/product_public_category.xml',
        'views/product_brand.xml',
        'views/product_label.xml',
        'views/product_pricelist_item.xml',
        'views/product_attribute.xml',
        'views/product_measure_attributes.xml',
        'templates/assets.xml',
        'wizards/product_brand_wizard_view.xml',
        'wizards/product_label_wizard_view.xml',
        'templates/template.xml',
        'templates/mega_menu.xml',
        'templates/pwa.xml',
        'templates/offilne.xml',
    ],

    'assets': {
        'web.assets_frontend': [
            'emipro_theme_base/static/src/js/frontend/**/*',
            'emipro_theme_base/static/src/snippets/s_searchbar/**/*',
            'emipro_theme_base/static/src/js/frontend/pwa_web.js',            
        ],
        'web_editor.assets_wysiwyg': [],
        'website.assets_editor': [],
    },

    # Author
    'author': 'Emipro Technologies Pvt. Ltd.',
    'website': 'https://www.emiprotechnologies.com',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',

    'images': [ 'static/description/emipro_theme_base.jpg'],

    # Technical
    'installable': True,
    'auto_install': False,
    'price': 50.00,
    'currency': 'USD',
}
