{
    'name': 'MH Base',
    'version': '18.0.1.0.0',
    'category': 'Inventory',
    'summary': 'Módulo base para sistema MH - Campos fundamentais',
    'description': """
        MH Base Module
        ==============

        Módulo fundação do sistema MH que define campos base para Purchase Order:
        - service_type: Classificação de tipo de serviço/produto
        - import_document_ids: Relação com documentos de importação
        - transformation_document_ids: Relação com documentos de transformação

        Este módulo deve ser a base de todos os outros módulos MH para evitar
        dependências circulares e garantir que os campos estejam sempre disponíveis.
    """,
    'author': 'MH',
    'depends': [
        'sale',
        'purchase',
        'stock',
        'account',
    ],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'data/decimal_precision_data.xml',
        'data/service_type_area_data.xml',
        'views/service_type_views.xml',
        'views/product_views.xml',
        'views/res_partner_views.xml',
        'views/account_move_views.xml',
        'views/account_payment_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
