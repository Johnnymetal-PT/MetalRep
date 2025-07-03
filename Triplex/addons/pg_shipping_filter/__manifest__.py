{
    'name': 'PG Partner Shipping Filter',
    'version': '1.0',
    'summary': 'Filter shipping addresses by selected client in Sales Orders',
    'description': 'Dynamically filters the shipping address selection based on the selected customer in Sales Orders.',
    'category': 'Sales',
    'author': 'Your Name',
    'depends': ['sale'],
    'data': [
        'views/sale_order_view.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
