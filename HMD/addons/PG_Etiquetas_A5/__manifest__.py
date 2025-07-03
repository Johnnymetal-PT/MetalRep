{
    'name': 'PG_Etiquetas_A5',
    'version': '1.0',
    'category': 'Inventory',
    'license': 'LGPL-3',
    'summary': 'Add functionality to print A5 product tags from product.product',
    'description': """
        This module adds a button in the product.product form view that allows users 
        to print product tags in A5 format. The tags include product details, logos, 
        and other relevant information.
    """,
    'author': 'Parametro Global',
    'website': 'http://www.parametroglobal.pt',

    'depends': ['base','product','stock', 'iot'],

    'data': [
        'security/ir.model.access.csv',
        'views/product_template_selector.xml',
        'views/stock_picking_button.xml',
        'views/wizard.xml',
    ],
    
    'installable': True,
    'application': False,
    'auto_install': False,
}
