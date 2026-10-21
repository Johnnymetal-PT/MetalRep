# -*- coding: UTF-8 -*-
# Part of Softhealer Technologies.
{
    "name": "All in One Multi Discount",
    "author": "Parametro Global",
    "version": "0.0.3",
    "license": "OPL-1",
    "category": "Extra Tools",
    "summary": "Sale Multi Discount",
    "description": """
Multi Discount Module, All In One Discount App Odoo.
""",
    "depends": [
        'sale',
        'sale_management',
        'purchase',
        'account'
        ],
    "data": [
        'security/sale_order_groups.xml',
        #'security/purchase_order_groups.xml',
        'security/account_move_groups.xml',
        'views/sale_order_views.xml',
        #'views/purchase_order_views.xml',
        'views/account_move_views.xml',
        'report/sale_order_templates.xml',
        #'report/purchase_order_templates.xml',
        'report/account_move_templates.xml',
    ],

    "images": ['static/description/background.png', ],
    "auto_install": False,
    "application": True,
    "installable": True,
    "price": 40,
    "currency": "EUR"
}
