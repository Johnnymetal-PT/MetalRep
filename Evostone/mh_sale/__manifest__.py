{
    "name": "MH Vendas",
    "version": "18.0.1.0.0",
    "depends": ["sale_stock", "stock", "account", "mh_picking", "mh_layout_pdf"],
    "category": "Sales",
    'author': 'Make It Happen, SA',
    'website': 'https://makeithappen.co.mz/pt',
    "summary": "Gestão de Vendas com Aprovação e Recibos Pró-forma",
    'description': """
        Módulo de Vendas personalizado criado pela empresa Make It Happen.

        Funcionalidades:

        * Sistema de aprovação de cotações
        * Gestão de Recibos Pró-forma de Clientes:

          - Registro de pagamentos antecipados
          - Alocação flexível (um pagamento pode cobrir múltiplas cotações)
          - Uma cotação pode receber múltiplos pagamentos
          - Controle de valores remanescentes
          - Detecção automática de pagamentos disponíveis

        * Controle de lotes em vendas
        * Workflow de aprovação com botões de aprovar/rejeitar
        * Validação dupla: cotação confirmada se aprovada OU com recibo pró-forma
    """,
    "data": [
        "security/security.xml",
        "data/sequence_data.xml",
        # "reports/proforma_invoice_report.xml",
        "views/sale_order_views.xml",
        "views/sale_margin_views.xml",
        "views/sale_config_settings_views.xml",
        "views/sale_order_rejection_wizard_views.xml",
        "views/sale_order_cancel_wizard_views.xml",
        "views/sale_order_margin_wizard_views.xml",
        "views/proforma_payment_views.xml",
        "views/proforma_payment_allocation_views.xml",
        "views/proforma_payment_dashboard_views.xml",
        "reports/stock_reservation_report_views.xml",
        "views/stock_available_wizard_views.xml",
        "wizards/proforma_to_payment_wizard_views.xml",
        "wizards/sale_create_proforma_wizard_views.xml",
        "security/ir.model.access.csv",
    ],
    "assets": {
        "web.assets_backend": [
            "mh_sale/static/src/js/lot_availability_widget.js",
            "mh_sale/static/src/xml/lot_availability_widget.xml",
            "mh_sale/static/src/js/kpi_card.js",
            "mh_sale/static/src/js/chart_renderer.js",
            "mh_sale/static/src/js/proforma_dashboard.js",
            "mh_sale/static/src/xml/proforma_dashboard_templates.xml",
            "mh_sale/static/src/scss/proforma_dashboard.scss",
            "mh_sale/static/src/js/stock_reservation_dashboard.js",
            "mh_sale/static/src/xml/stock_reservation_dashboard_templates.xml",
        ],
    },
    "installable": True,
    "auto_install": False,
    "application": False,
    'license': 'LGPL-3',
}