{
    'name': 'MH Transformação de Produtos',
    'version': '18.0.1.0.0',
    'category': 'Inventory',
    'author': 'Make It Happen, SA',
    'website': 'https://makeithappen.co.mz/pt',
    'summary': 'Gestão de transformação de produtos',
    'description': """
    Módulo para gestão de transformação de produtos:
    - Controle de transformadores externos
    - Documentos de transformação com workflow completo
    - Transformação de blocos em placas e placas em bandas
    - Controle de stock automático
    - Rastreabilidade completa do processo
    """,
    'depends': ['mh_base', 'mh_inventory', 'mh_stock_valuation', 'stock_landed_costs', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/stock_location_views.xml',
        'views/product_template_views.xml',
        'views/res_partner_views.xml',
        'views/transformation_stock_wizard_views.xml',
        'views/transformation_document_views.xml',
        'views/stock_picking_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
    'license': 'LGPL-3',
}