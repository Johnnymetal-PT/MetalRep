{
    'name': 'pg_packing_list',
    'version': '1.0',
    'summary': 'Add volume in shipping process',
    'description': 'Add volume in shipping process.',
    'category': 'Inventory',
    'depends': ['base', 'product', 'stock'], 
    'data': [
        'views/qweb_report.xml',
        'report/report_stockPicking_template.xml',
    ],
    'installable': True, 
    'auto_install': False,               
    'application': False,               
}
