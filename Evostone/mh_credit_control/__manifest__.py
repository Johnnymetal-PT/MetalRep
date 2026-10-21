{
    'name': 'MH Credit Control',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Controle de crédito e aprovação de vendas',
    'description': """
        Módulo para controle de crédito do cliente com:
        - Bloqueio de vendas quando limite de crédito excedido
        - Bloqueio quando cliente tem facturas vencidas
        - Bloqueio quando cliente tem facturas pendentes
        - Sistema de aprovação por tipo com histórico
        - Grupos de aprovação separados para cada tipo
    """,
    'author': 'MH',
    'depends': [
        'mh_sale',  # Depende do mh_sale para integração com workflow de aprovação
        'account',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizards/credit_block_wizard_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
