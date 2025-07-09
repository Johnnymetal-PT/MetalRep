{
    'name': 'PG Dynamic Consumption Table for Manufacturing Orders',
    'version': '1.0',
    'summary': 'Fetch and apply dynamic consumption values from product backoffice in Manufacturing Orders',
    'sequence': 1,
    'description': """
        This module dynamically applies the correct 'Para Consumir' values in Manufacturing Orders based on 
        the product's backoffice data for 'Tecido de Fornecedor'.
    """,
    'category': 'Manufacturing',
    'author': 'Your Name',
    'depends': ['mrp', 'stock'],
    'data': [
        'views/product_template_views.xml',  # Add the consumption table field to the product backoffice
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}

