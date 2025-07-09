{
    'name': 'PG Tecidos Customization',
    'version': '1.0',
    'summary': 'Module to handle the customization of products in Manufacturing Orders based on product description variants',
    'depends': ['mrp', 'stock'],
    'data': [
        'views/pg_tecidos_view.xml',
        'data/groups.xml',
    ],
    'installable': True,
    'application': False,
}

