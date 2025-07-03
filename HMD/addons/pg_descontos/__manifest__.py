{
    'name': 'PG Descontos',
    'version': '1.0',
    'summary': 'Automatically apply a tag "Desconto" for products in the "Descontos" pricelist.',
    'category': 'Sales',
    'author': 'Your Name',
    'depends': ['product', 'sale'],
    'data': [
        'data/pg_descontos_cron.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
