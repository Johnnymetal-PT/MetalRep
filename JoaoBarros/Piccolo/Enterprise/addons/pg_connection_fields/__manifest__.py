{
    'name': 'PG Stock Picking SO Reference',
    'version': '1.0',
    'summary': 'Fetch customer and reference from the original Sales Order',
    'author': 'Your Name',
    'depends': ['stock', 'purchase', 'sale', 'mrp', 'account'],
    'data': [
        'views/stock_picking_views.xml',
        'views/account_payment_views.xml',
    ],
    'installable': True,
    'application': False,
}
