# Copyright 2025 MH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "MH Multiple Discount",
    "version": "18.0.1.3.0",
    "category": "Sales",
    "author": "MH",
    "license": "AGPL-3",
    "summary": "Manage multiple discounts on sale and invoice lines",
    "depends": [
        "mh_sale",
        "sale_management",
        "account",
        "purchase_stock",
    ],
    "data": [
        "views/sale_order_views.xml",
        "views/account_move_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "mh_multiple_discount/static/src/xml/tax_totals.xml",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": True,
}
