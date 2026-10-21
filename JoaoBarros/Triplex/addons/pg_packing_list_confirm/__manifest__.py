{
    'name': 'pg_packing_list_confirm',
    'version': '1.0',
    'summary': 'Require packing list confirmation for deliveries',
    'description': 'Adds a packing list confirmation toggle that blocks delivery validation until confirmed.',
    'category': 'Inventory',
    'depends': ['stock'],
    'data': [
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
