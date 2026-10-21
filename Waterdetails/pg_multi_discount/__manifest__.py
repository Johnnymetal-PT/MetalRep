{
    "name": "PG Multi Discount",
    "author": "Parametro Global",
    "website": "https://www.parametroglobal.pt",
    "support": "engenharia@hubel.pt",
    "version": "19.0.1.0.5",
    "license": "OPL-1",
    "category": "Sales",
    "summary": "Multiple progressive discounts on Sales, Purchase and Invoices",
    "description": """
PG Multi Discount
=================

Module to apply multiple progressive discounts in commercial and financial processes.

Key Features
--------------------------
- Multiple discounts on sales, purchase, and invoice lines.
- Calculation of discounted unit value, unit total, and total discounted value.
- Integration with `product.supplierinfo` to reuse vendor discounts.
- Updates reports and documents to reflect the applied discount structure.
- Supports teams that need to negotiate with multiple chained percentages.
""",
    "depends": [
        "sale_management",
        "purchase",
        "account"
    ],
    "data": [
        "security/sale_order_groups.xml",
        "security/purchase_order_groups.xml",
        "security/account_move_groups.xml",
        "views/sale_order_views.xml",
        "views/purchase_order_views.xml",
        "views/account_move_views.xml",
        "views/product_supplierinfo_views.xml",
        "report/sale_order_templates.xml",
        "report/purchase_order_templates.xml"
    ],
    "images": ["static/description/background.png"],
    "auto_install": False,
    "application": False,
    "installable": True
}
