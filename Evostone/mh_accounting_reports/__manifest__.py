{
    'name': 'MH Accounting Reports',
    'version': '18.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Customizações de relatórios contabilísticos',
    'description': """
        Módulo de customização de relatórios contabilísticos:
        - Calendário de Depreciação: coluna Taxa %
        - Renomear para "Mapa das Reintegrações e Amortizações"
        - Traduzir cabeçalhos para português (Valores de Aquisição, Reintegrações e Amortizações)
    """,
    'author': 'Make It Happen',
    'depends': ['account_asset', 'account_reports', 'mh_stone_reports'],
    'data': [
        "security/ir.model.access.csv",
        'data/assets_report_customization.xml',
        "data/aged_customer_invoices.xml",
        "data/aged_supplier_invoices.xml",
        "data/pdf_export_templates.xml",
        "data/pdf_export_payment_templates.xml",
        "data/email_template_partner_statement.xml",
        "data/email_template_partner_payment.xml",
        "wizards/partner_statement_action_wizard_views.xml",
        "wizards/partner_payment_action_wizard_views.xml",
        "wizards/map_mail_composer_views.xml",
        "views/res_config_settings_views.xml",
        "views/menu.xml",
        "views/res_partner_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "mh_accounting_reports/static/src/components/line_cell.js",
            "mh_accounting_reports/static/src/components/line_cell.xml",
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',
}
