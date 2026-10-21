{
    'name': 'PG Controlled Payment Methods For Product Categories',
    'version': '1.0',
    'summary': 'Block certains products for any payment methods.',
    'description': 'Block certains products for any payment methods.',
    'depends': ['base', 'product', 'payment', 'website_sale'], 
    'data': [
        'views/product_template_view.xml',
        'views/payment_views.xml',
    ],
    'installable': True, 
    'auto_install': False,               
    'application': False,               
}
