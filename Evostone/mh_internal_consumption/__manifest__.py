{
    'name': 'MH Consumo Interno',
    'version': '18.0.1.0.0',
    'category': 'Inventory',
    'summary': 'Gestão de consumo interno de produtos consumíveis',
    'description': """
        Consumo Interno de Produtos
        ===========================

        Funcionalidades:
        - Registo de consumo interno de materiais (escritório, limpeza, etc.)
        - Verificação de stock ao confirmar
        - Saída automática do stock ao concluir (localização tipo Customer com visto Consumo Interno)
        - Grupos de segurança: utilizador e responsável
    """,
    'author': 'Make It Happen, SA',
    'website': 'https://makeithappen.co.mz/pt',
    'depends': ['stock', 'product', 'mh_inventory'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/stock_location_views.xml',
        'views/internal_consumption_views.xml',
        'views/material_consumption_views.xml',
        'views/menu_items.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mh_internal_consumption/static/src/js/consumption_availability_widget.js',
            'mh_internal_consumption/static/src/xml/consumption_availability_widget.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
