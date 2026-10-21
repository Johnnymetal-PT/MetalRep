{
    'name': 'MH Sale Order Validity',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Sistema de validade para cotações com expiração automática',
    'description': """
        Sale Order Validity Management
        ================================

        Funcionalidades:
        - Data de validade automática para cotações (60 dias)
        - Estados: Válida, Expirando, Expirada
        - Renovação de validade
        - Verificação automática diária (cron)
        - Bloqueio de confirmação de cotações expiradas
        - Badges visuais e filtros
    """,
    'author': 'Make It Happen, SA',
    'website': 'https://makeithappen.co.mz/pt',
    'depends': ['mh_sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/sale_order_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
