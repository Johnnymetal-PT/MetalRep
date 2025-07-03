# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'PG Website Product Attribute Image',
    'summary': 'Adding images to attribute values. (website attribute image | product image)',
    'description': 'Adding images to attribute values',
    'version': '17.0.1.0',
    'category': 'Website',
    'author': 'Visionee',
    'license': 'OPL-1',
    'depends': [
        'website_sale', 'stock', 'sale_product_configurator',
    ],
    'data': [
        'templates/shop_product.xml',
        'views/product_attribute_value_views.xml',
    ],
    'assets': {
        #'web.assets_frontend': [
        #    'pg_website_attribute_image/static/src/**/*',
        #],
        'web.assets_backend': [
            'pg_website_attribute_image/static/src/xml/product.xml',
        ],
    },
    'images': [
        'static/description/banner.gif',
    ],
    'price': 20,
    'currency': "EUR",
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
}
