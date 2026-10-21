# -*- coding: utf-8 -*-
{
    'name': 'MH Sale Pricelist Lot Integration',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Integrate pricelists with lot groups for flexible lot-based pricing',
    'description': """
MH Sale Pricelist Lot Integration
==================================

This module extends Odoo's pricelist system to support lot-based pricing rules.

Features:
---------
* Add pricelist rules based on Base Lot Groups
* Add pricelist rules based on Lot Price Groups (specific dimensions)
* Hybrid pricing system:
  - Priority 1: Pricelist rules for lot groups
  - Priority 2: Direct lot price (fallback to existing behavior)
  - Priority 3: Standard pricelist rules (product/category/global)

* Supports all standard pricelist features:
  - Discounts and markups
  - Fixed prices
  - Minimum quantities
  - Date ranges
  - Formulas

Use Cases:
----------
* VIP customer discounts on specific lot groups
* Promotional pricing for lots with specific dimensions
* Volume discounts by lot group
* Seasonal pricing adjustments
* Size-based premium pricing

Technical:
----------
* Extends product.pricelist.item with new applied_on options
* Passes lot_id through pricelist computation
* Maintains backward compatibility with existing pricing
    """,
    'author': 'Make It Happen, SA',
    'website': 'https://www.makeithappen.pt',
    'license': 'LGPL-3',
    'depends': [
        'product',       # Base pricelist functionality
        'sale',          # Sale order line pricing
        'mh_sale',       # lot_id field in sale.order.line
        'mh_picking',    # base.lot.group and lot.price.group models
    ],
    'data': [
        'views/product_pricelist_item_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
