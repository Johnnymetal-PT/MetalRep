{
    'name': 'PG Tecidos Customization',
    'version': '18.0.1.0.0',
    'summary': 'Module to handle the customization of products in Manufacturing Orders based on product description variants',
    'depends': ['mrp', 'stock', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/pg_tecidos_view.xml',
        'views/mrp_zero_qty_warning_view.xml',
    ],
    'installable': True,
    'application': False,
}

