{
    'name': 'MZ Localization',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Localizations',
    'summary': 'Localizacao Mocambique - Apuramento Fiscal IRPC',
    'description': '''
        Modulo de localizacao para Mocambique.
        Inclui modelos para apuramento fiscal IRPC, alvaras, CAE, etc.
    ''',
    'author': 'Innovactive',
    'depends': ['account', 'mail', 'hr_payroll'],
    'data': [
        'security/ir.model.access.csv',
        # Views por modelo
        'views/account_move_views.xml',
        'views/alvara_model_views.xml',
        'views/apuramento_model_views.xml',
        'views/apuramento_template_model_views.xml',
        'views/bank_statement_views.xml',
        'views/cae_model_views.xml',
        'views/modelo_onze_views.xml',
        'views/payment_register_views.xml',
        'views/report_account_model_views.xml',
        'views/report_m20_views.xml',
        'views/res_company_views.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml',
        # Menus e acoes
        'views/menus.xml',
        # Reports por categoria
        'reports/report_invoice.xml',
        'reports/report_sale.xml',
        'reports/report_purchase.xml',
        'reports/report_delivery.xml',
        'reports/report_payment.xml',
        'reports/report_fiscal.xml',
        'reports/report_employee.xml',
        'reports/report_other.xml',
        # Report Actions
        'reports/report_actions.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
