{
    'name': 'PG_Etiquetas_A4',
    'version': '2.0',
    'category': 'Inventory',
    'summary': 'Add functionality to print A4 product tags from stock picking',
    'description': """
        This module adds a button in the Stock Picking form view that allows users 
        to print product tags in A4 format. The tags include product details, logos, 
        and other relevant information.
    """,
    'author': 'Parametro Global',
    'website': 'http://www.parametroglobal.pt',

    'depends': ['base', 'product', 'stock', 'sale'],
    
    'data': [
        'views/product_template_view.xml',
        'views/product_product_view.xml',
        'views/stock_picking_view.xml',
        'views/report_product_labels_a4.xml',
        'reports/report_stock_template.xml',
        'reports/report_stock_product.xml',
        'reports/report_stock_picking.xml',
    ],
    
    'installable': True,
    'application': False,
    'auto_install': False,
}
