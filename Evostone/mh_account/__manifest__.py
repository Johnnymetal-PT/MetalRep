{
    'name': 'MH Contabilidade',
    'version': '18.0.2.0.0',
    'category': 'Accounting',
    'summary': 'Customizações contabilísticas com gestão de recibos',
    'description': """
        Módulo de customização para Contabilidade
        ==========================================

        Funcionalidades:
        - Numeração automática de recibos por diário e ano
        - Formato: REC/{CÓDIGO_DIÁRIO}/{ANO}/{NÚMERO}
        - Validação de ordem cronológica para recebimentos
        - Bloqueio de eliminação de pagamentos com recibo
        - Contas externas para parceiros estrangeiros
    """,
    'author': 'MH',
    'website': '',
    'depends': ['account', 'product', 'stock_account', 'account_auto_transfer'],
    'data': [
        'security/ir.model.access.csv',
        'data/cleanup_advance_views.xml',  # Limpa views antigas de adiantamento
        'data/mail_template_data.xml',
        # 'data/sequence_data.xml',  # Sequências não usadas - numeração manual
        # 'wizard/account_advance_apply_wizard_views.xml',  # Adiantamentos comentados
        'wizard/account_payment_register_views.xml',
        'views/account_payment_receipt.xml',
        # 'views/account_payment_advance.xml',  # Adiantamentos comentados
        'views/account_move_views.xml',
        'views/account_transfer_model_views.xml',
        'views/product_category_views.xml',
        'views/product_template_views.xml',
        # 'views/product_product_views.xml',  # Contas de variante removidas - usar contas do template
        'views/payment_receipt_report.xml',
        'views/account_journal_dashboard_views.xml',
        'views/menus_items.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mh_account/static/src/css/journal_dashboard.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
