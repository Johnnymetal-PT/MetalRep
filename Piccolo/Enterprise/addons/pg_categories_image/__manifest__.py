# __manifest__.py
{
    'name': 'PG Category Images',
    'version': '1.0',
    'category': 'Website',
    'summary': 'Adds additional images to product categories and products with animation',
    'depends': ['website_sale'],
    'data': [
        'views/product_category_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
