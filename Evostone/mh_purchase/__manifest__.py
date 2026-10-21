{
    'name': 'MH Compras',
    'version': '18.0.2.0.3',
    'category': 'Inventory/Purchase',
    'summary': 'Gestão de Compras com AVCO e custos de destino standard',
    'description': """
        Módulo de Gestão de Compras
        ============================

        Funcionalidades:
        - Custo Médio (AVCO) standard do Odoo
        - Custos de destino standard do Odoo
        - Consulta do histórico do antigo Documento de Importação
        - Suporte completo a lotes
        - Integração com stock.valuation.layer

        Fluxo:
        1. Confirmar o pedido de compra
        2. Validar a receção standard
        3. Registar custos adicionais nas faturas de fornecedor
        4. Criar, calcular e validar o custo de destino
    """,
    'author': 'MH',
    'depends': [
        'mh_base',
        'base',
        'stock',
        'sale_stock',
        'stock_account',
        'stock_landed_costs',  # Para criar stock.landed.cost no Import Document
        'purchase',
        'product',
        'mail',
        'mh_product_transformation',
        'mh_picking',
        'mh_stock_valuation',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/product_product_views.xml',
        'views/product_category_views.xml',
        'views/import_document_views.xml',
        'views/purchase_order_views.xml',
        'views/res_partner_views.xml',
        'views/stock_move_views.xml',
        'views/stock_valuation_views.xml',
        'views/stock_picking_views.xml',
        'views/menu_views.xml',
        'wizard/purchase_confirm_wizard_views.xml',
        'wizard/sticker_print_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mh_purchase/static/src/fields/stock_move_line_x2_many_field_extend.js',
        ],
    },
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
