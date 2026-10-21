{
    'name': 'PG Obras',
    'version': '18.0.0.0',
    'summary': 'Gestão de armazém e localizações para obras.',
    'author': 'Parametro Global',
    'license': 'LGPL-3',
    'depends': ['stock', 'purchase', 'account', 'project'],
    'data': [
        'data/warehouse.xml',
        'data/locations.xml',
        'data/sequences.xml',
        'data/picking_types.xml', 
        'views/res_partner_views.xml',
        'views/account_move_views.xml',
        'views/stock_warehouse_views.xml',
    ],
    # RECOMENDADO para não duplicar em BD real que já tenha estes registos:
    'pre_init_hook': 'pre_init_hook',
    'installable': True,
    'application': False,
}

