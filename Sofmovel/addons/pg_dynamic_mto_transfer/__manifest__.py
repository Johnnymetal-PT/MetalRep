{
    "name": "PG Dynamic MTO Transfer",
    "version": "17.0.1.0.0",
    "depends": ["stock", "purchase", "sale_stock"],
    "author": "Parâmetro Global",
    "category": "Inventory",
    "description": "Creates internal transfers before PO in MTO logic and enhances Sale Order views.",
    "installable": True,
    "auto_install": False,
    "data": [
        "views/sale_order_view.xml"
    ]
}