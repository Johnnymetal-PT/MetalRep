# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'PG Website Product Attribute Image',
    'summary': 'Adding images to attribute values. (website attribute image | product image)',
    'description': 'Adding images to attribute values',
    'version': '18.0.1.0.0',
    'category': 'Website',
    'author': 'Visionee',
    'license': 'AGPL-3',
    'depends': [
        'website_sale', 'stock',
    ],
    'data': [
        'templates/shop_product.xml',
        'views/product_attribute_value_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'pg_website_attribute_image/static/src/css/pg_attribute_image_dropdown.css',
            'pg_website_attribute_image/static/src/js/pg_attribute_image_dropdown.js',
        ],
    },
    'images': [
        'static/description/banner.gif',
    ],
    'price': 20,
    'currency': "EUR",
    'installable': True,
    'auto_install': False,
}

