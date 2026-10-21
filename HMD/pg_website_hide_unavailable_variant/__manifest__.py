# -*- coding: utf-8 -*-
{
    'name': "PG Hide Unavailable Variants",

    'summary': """
        Hide Unavailable Variants on the website""",
    'description': """ This module gives option to hide the variants form the website by simply enabling a
    boolean field. Here no need to set the exclusions. So customer can only see the valid and available attribute 
    values for the product.
    Hide Variants,
    Hide Attribute Values,
    Odoo Hide Variants,
    Hide Product Variants """,

    'author': "ErpMstar Solutions",
    'category': 'eCommerce',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['website_sale_stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'pg_website_hide_unavailable_variant/static/src/js/hide.js',
        ]
    },
    # only loaded in demonstration mode
    'installable': True,
    'application': True,
    'images': ['static/description/banner.gif'],
    'installable': True,
    'application': True,
    'price': 40,
    'currency': 'EUR',
}
