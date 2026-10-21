{
    'name': 'MH Partner Account',
    'version': '18.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Criação automática de contas contabilísticas para parceiros',
    'description': '''
        Módulo para criar automaticamente contas contabilísticas (a receber e a pagar)
        para clientes e fornecedores baseado em configurações da empresa.

        Funcionalidades:
        - Configuração de prefixos e sequências por empresa
        - Criação automática ou com confirmação do utilizador
        - Numeração sequencial de clientes e fornecedores
        - Suporte para diferentes tipos de parceiros (Nacional, Estrangeiro, etc.)
    ''',
    'author': 'MH',
    'depends': ['base', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_company_views.xml',
        'views/res_users_views.xml',
        'views/res_partner_views.xml',
        'wizards/partner_account_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mh_partner_account/static/src/css/partner_numbers.css',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
