{
    'name': 'PG Volume In Shipping',
    'version': '2.0',
    'summary': 'Add volume in shipping process',
    'description': 'Add volume in shipping process.',
    'category': 'Inventory',
    'depends': ['base', 'product', 'stock'], 
    'data': [
        'views/product_volume_view.xml',
        'views/qweb_report.xml',
        'report/report_deliveryslip_template.xml'
    ],
    'installable': True, 
    'auto_install': False,               
    'application': False,               
}