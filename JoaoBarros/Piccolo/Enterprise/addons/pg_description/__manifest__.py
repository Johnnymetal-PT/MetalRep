{
    "name": "PG Description Enhancements",
    "version": "1.1",
    "summary": "Dynamically process and display descriptions for sales orders based on product variants.",
    "author": "Your Name",
    "website": "https://yourwebsite.com",
    "category": "Sales",
    "depends": [
        "sale",  # Core sales module
        "website_sale",  # Required if this affects the website shop
    ],
    "description": """
        This module dynamically processes the product description in sales orders 
        and ensures the description reflects accurate variant selections in the cart, 
        checkout, and sales order lines.
        
        Key Features:
        - Automatically updates product descriptions in sales orders.
        - Provides processed descriptions for the website cart and checkout views.
        - No need to manually modify existing sales order views.
    """,
    "data": [
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}

