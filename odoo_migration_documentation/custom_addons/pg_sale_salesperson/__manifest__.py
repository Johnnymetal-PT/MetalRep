{
    "name": "PG Sale Salesperson",
    "version": "18.0.1.0.0",
    "author": "PG",
    "category": "Sales",
    "summary": "Adds salesperson partner fields to sale orders and partners",
    "depends": ["sale_management", "contacts"],
    "data": [
        "views/sale_order_views.xml",
        "views/res_partner_views.xml",
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": False,
}
