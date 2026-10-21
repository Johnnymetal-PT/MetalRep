# -*- coding: UTF-8 -*-
# Part of Softhealer Technologies.
{
    "name": "All in One Multi Discount",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "version": "18.0.1.0.0",
    "license": "OPL-1",
    "category": "Extra Tools",
    "summary": "Sale Multi Discount Accounting Multi Discount Purchase Multi Discount Request For Quotation Multi Discount All In One Discount RFQ Discount SO Multi Discount PO Discount Multiple discount offer discount double discounts deals Odoo Sale order Multi Discount Accounting Multiple Discount Purchase order Multi Discount Sale Order Multiple Discount Purchase Order Multiple Discount Invoice Order Multiple Discount All in One Multi Discount - Sale, Accounting, Purchase Multiple Discount Selection Multiple Discounts selection Multi Discount Selection Multi Discounts Selection Add Multi Discounts Add Multiple Discounts Sales Discounts Sale Discounts Trade Discounts Fixed Discounts Cash Discounts Threshold Discounts Percentage Discounts Set Discounts Manage Discounts Offer Discounts Customer Wise Discount Purchase Discounts Invoice Discounts All In One Discounts All In One Multiple Discounts All In One Multi Discounts Discount on Purchase Discount on Sales Discount on Invoices Purchase Order Discount Sale Order Discount Sales Order Discount Manage Discounts Special Discount  On Reports  Vendor Bill Discount Customer Invoices Discount Odoo",
    "description": """
Currently, in odoo, you can add only one discount on price If you want to add
another discount at a discounted price? Don't worry here we build a module
that can help to add multiple discounts on the price. With this module you can
pass a Sales/Invoice with various discounts like Scheme Discount,
Cash discount, Special Discount for any item, also you can print multiple
discounts in a pdf report.
All In One Multi Discount – Sale, Accounting, Purchase Odoo.
Multiple Discount In Price Module, All In One Discount In Sales,
Multi Discount in Accounting On Price Odoo,
All In One Discount In Purchase Order Odoo.
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
        #'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/account_move_views.xml',
        #'report/sale_order_templates.xml',
        #'report/purchase_order_templates.xml',
        #'report/account_move_templates.xml',
    ],

    "images": ['static/description/background.png', ],
    "auto_install": False,
    "application": True,
    "installable": True,
    "price": 40,
    "currency": "EUR"
}
