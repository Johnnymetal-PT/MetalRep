{
    'name': 'MH Stone Reports',
    'version': '18.0.1.0.6',
    'category': 'Reporting',
    'summary': 'Relatorios customizados Stone Trading',
    'description': '''
        Modulo que contem todos os relatorios customizados do Studio para Stone Trading.
        
        Total: 160 views organizadas em:
        - reports/sale/ - Relatorios de Vendas (8 views) + Product Matrix (4 views)
        - reports/purchase/ - Relatorios de Compras (6 views)
        - reports/account/ - Relatorios de Facturas (10), Pagamentos (7) e Outros (6)
        - reports/hr/ - Relatorios de RH/Payslip (6 views)
        - reports/stock/ - Relatorios de Stock (7 views)
        - reports/fiscal/ - Relatorios Fiscais (10 views)
        - reports/website/ - Views de Website (16 views)
        - reports/other/ - Outros Relatorios (80 views)
    ''',
    'author': 'MH',
    # `account_MZ` retirado em 04/09/2026. A dependencia era declarativa e sem
    # uso: uma varredura ao modulo inteiro devolve uma unica ocorrencia do nome,
    # a desta linha. Mantê-la fazia a desinstalacao da localizacao mocambicana
    # arrastar tambem estes relatorios, que sao do negocio da pedra.
    #
    # NAO leva bump de versao de proposito. O `ir.module.module.update_list()`
    # rele os manifestos de todos os modulos detectados e reescreve as linhas de
    # `ir_module_module_dependency` (ver `_update_dependencies`, que faz DELETE
    # das que sairam). Basta actualizar a lista de aplicacoes. Um bump forcaria
    # um upgrade do modulo, e o `b47e0f8` deste repo mostra o que isso custa.
    'depends': ['base', 'sale', 'purchase', 'account', 'stock', 'hr_payroll', 'website', 'mh_multiple_discount', 'mh_sale', 'mh_stock_valuation', 'mh_stock_at_date'],
    'data': [
        # Security
        'security/ir.model.access.csv',
        'security/security_groups.xml',
        # Views (devem ser carregados primeiro)
        'views/res_company_views.xml',
        'views/res_config_settings_views.xml',
        # Wizards
        'wizards/stone_stock_report_wizard_views.xml',
        'wizards/stone_sticker_print_wizard_views.xml',
        # Dados base (paperformats, etc.) - devem ser carregados primeiro
        'data/paperformat_data.xml',
        # Templates QWeb (views)
        # Sale - Quotation templates
        'reports/sale/quotation/quotation_reports.xml',
        # Sale - PRÓ-FORMA templates
        'reports/sale/ft_proforma/proforma_reports.xml',
        # Sale - Recibo Pró-Forma (proforma.payment)
        'reports/sale/proforma_payment/proforma_payment_reports.xml',
        # Sale - Cotação Detalhada templates
        'reports/sale/detailed_quotation/detailed_quotation_reports.xml',
        # 'reports/sale/sale_reports.xml',
        'reports/sale/product_matrix_reports.xml',
        'reports/purchase/purchase_reports.xml',
        # Stock - Guia de Movimentação (stock.picking)
        'reports/stock/delivery_guide/delivery_guide_reports.xml',
        # Stock - Serial Nr. (stock.move)
        'reports/stock/serial_nr/serial_nr_reports.xml',
        # Stock - Stickers de Placas (stock.move.line)
        'reports/stock/stickers/stickers_reports.xml',
        # Stock - Stickers de Placas ZPL (stock.move.line) - Zebra ZD421
        'reports/stock/stickers/stickers_zpl_reports.xml',
        'reports/stock/stone_stock/stone_stickers_zpl_reports.xml',
        # Stock - Stock de Pedras (stone.stock)
        'reports/stock/stone_stock/stone_stock_reports.xml',
        # Stock - Listagem de Stock (wizard)
        'reports/stock/stone_stock/stone_stock_listing_reports.xml',
        # Stock - Guia de Recepção de Pedras (stock.picking)
        'reports/stock/picking/picking_reports.xml',
        # Account - Factura (account.move - out_invoice)
        'reports/account/invoice/invoice_reports.xml',
        # Account - Nota de Credito (account.move - out_refund)
        'reports/account/invoice/credit_note_reports.xml',
        # Account - Nota de Debito (account.move)
        'reports/account/invoice/debit_note_reports.xml',
        # Account - Recibo/Nota de Pagamento (account.payment)
        'reports/account/payment/payment_receipt_reports.xml',
        'reports/account/account_other_reports.xml',
        'reports/hr/payslip_reports.xml',
        'reports/fiscal/fiscal_reports.xml',
        'reports/website/website_reports.xml',
        'reports/other/other_reports.xml',
        # Actions (ir.actions.report) - devem ser carregados depois dos templates
        # Sale - Cotações
        'reports/sale/quotation/quotation_actions.xml',
        # Sale - Fatura PRÓ-FORMA
        'reports/sale/ft_proforma/proforma_actions.xml',
        # Sale - Recibo Pró-Forma (proforma.payment)
        'reports/sale/proforma_payment/proforma_payment_actions.xml',
        # Sale - Cotação Detalhada
        'reports/sale/detailed_quotation/detailed_quotation_actions.xml',
        'reports/purchase/purchase_actions.xml',
        # Account - Factura
        'reports/account/invoice/invoice_actions.xml',
        # Account - Nota de Credito
        'reports/account/invoice/credit_note_actions.xml',
        # Account - Nota de Debito
        'reports/account/invoice/debit_note_actions.xml',
        # Account - Recibo/Nota de Pagamento (account.payment)
        'reports/account/payment/payment_receipt_actions.xml',
        # Stock - Guia de Movimentação
        'reports/stock/delivery_guide/delivery_guide_actions.xml',
        # Stock - Serial Nr.
        'reports/stock/serial_nr/serial_nr_actions.xml',
        # Stock - Stickers de Placas
        'reports/stock/stickers/stickers_actions.xml',
        # Stock - Stickers de Placas ZPL - Zebra ZD421
        'reports/stock/stickers/stickers_zpl_actions.xml',
        # Stock - Stock de Pedras (stone.stock) - 3 reports
        'reports/stock/stone_stock/stone_stock_actions.xml',
        # Stock - Lista de Preços de Pedras (relatório interactivo)
        'reports/stock/stone_stock/stone_pricelist_report_templates.xml',
        # Stock - Valorização de Stock à Data (relatório interactivo)
        'reports/stock/stone_stock/stock_valuation_report_templates.xml',
        # Stock - Artigos sem Stock (relatório interactivo)
        'reports/stock/stone_stock/stock_no_stock_report_templates.xml',
        # Stock - Listagem de Stock (wizard)
        'reports/stock/stone_stock/stone_stock_listing_actions.xml',
        # Stock - Guia de Recepção de Pedras (stock.picking)
        'reports/stock/picking/picking_actions.xml',
        'reports/hr/payslip_actions.xml',
        'reports/other/other_actions.xml',
        # Mail templates (devem ser carregados depois das actions)
        'data/mail_template_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mh_stone_reports/static/src/zebra_print_action.js',
            'mh_stone_reports/static/src/js/stone_pricelist_report/stone_pricelist_report.js',
            'mh_stone_reports/static/src/js/stone_pricelist_report/stone_pricelist_report.xml',
            'mh_stone_reports/static/src/js/stock_valuation_report/stock_valuation_report.js',
            'mh_stone_reports/static/src/js/stock_valuation_report/stock_valuation_report.xml',
            'mh_stone_reports/static/src/js/stock_valuation_report/stock_valuation_report.css',
            'mh_stone_reports/static/src/js/stock_no_stock_report/stock_no_stock_report.js',
            'mh_stone_reports/static/src/js/stock_no_stock_report/stock_no_stock_report.xml',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
    'external_dependencies': {
        'python': ['barcode'],
    },
}
