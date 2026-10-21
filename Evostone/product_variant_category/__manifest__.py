# -*- coding: utf-8 -*-
{
    'name': 'Product Variant Category',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Allow independent category per product variant',
    'description': """
        This module allows each product variant to have its own category,
        independent from the product template category.

        If no variant category is set, it inherits from the template.
    """,
    'author': 'Innovactive',
    'website': 'https://www.innovactive.co.mz',
    'depends': ['product'],
    'data': [
        'views/product_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
