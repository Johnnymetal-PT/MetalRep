{
    'name': 'PG_Etiquetas_zpl',
    'version': '18.0.1.0.0',
    'category': 'Inventory',
    'license': 'LGPL-3',
    'summary': 'Print stock picking ZPL labels directly through IoT',
    'description': """
        This module adds a button on stock pickings that renders a ZPL label
        and sends it directly to an IoT printer.
    """,
    'author': 'Parametro Global',
    'website': 'http://www.parametroglobal.pt',

    'depends': ['base', 'product', 'stock', 'iot'],

    'data': [
        'views/stock_picking_button.xml',
    ],
    
    'installable': True,
    'application': False,
    'auto_install': False,
}
