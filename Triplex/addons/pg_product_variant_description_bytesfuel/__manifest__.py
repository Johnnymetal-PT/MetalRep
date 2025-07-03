# -*- coding: utf-8 -*-

{
    "name": "PG Website Product Variant Description",
    "version": "17.0.1.0",
    'author':'Bytesfuel',
    'website':'https://bytesfuel.com/',
    "category": "eCommerce",
    "description": """eCommerce Product Variant Description On Website""",
    "depends": ['website_sale'],
    'data': [
        'views/templates.xml',
        'views/product_variant_view.xml',
    ],

    'assets': {
        'web.assets_frontend': [
            '/pg_product_variant_description_bytesfuel/static/src/js/mixin.js',
        ],
    },

    "images": ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'license': 'OPL-1',
    'price': 10.00,
    'currency': 'USD',
}
