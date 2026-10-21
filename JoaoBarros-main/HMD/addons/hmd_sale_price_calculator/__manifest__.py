{
    "name": "HMD Sale Price Calculator",
    "version": "18.0.1.0.0",
    "author": "HMD",
    "website": "https://www.hmd.pt",
    "category": "Sales",
    "summary": "Interactive price calculator on sale order lines.",
    "license": "LGPL-3",
    "depends": ["sale", "purchase", "mrp"],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_order_views.xml",
        "wizard/sale_order_line_price_calculator_views.xml",
    ],
    "installable": True,
}
