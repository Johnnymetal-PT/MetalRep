{
    'name': 'MH Picking',
    'version': '18.0.1.0.0',
    'category': 'Inventory',
    'author': 'Make It Happen, SA',
    'website': 'https://makeithappen.co.mz/pt',
    'summary': 'Gestão de Dimensões Físicas de Produtos e Lotes',
    'description': """
    Módulo de Dimensões de Produtos e Lotes
    ========================================

    Funcionalidades:
    - Campos de dimensões (Comprimento, Largura, Espessura) para produtos
    - Campos de dimensões para lotes
    - Integração com mh_purchase

    Este módulo é instalado automaticamente com mh_purchase.
    """,
    'depends': [
        'mh_stock_valuation',  # Consolidado - base.lot.group e lot.price.group vêm daqui
        'purchase',
        'stock',
        'stock_barcode',
        'sale',
        'account',
        'mh_product_transformation',
        'stock_restrict_lot',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/scrap_location_data.xml',
        'views/product_template_views.xml',
        'views/product_product_views.xml',
        'views/stock_lot_views.xml',
        # base_lot_group_views.xml e lot_price_group_views.xml removidos - vêm do mh_stock_valuation
        'views/stock_move_views.xml',
        'views/stock_move_line_views.xml',
        'views/stock_picking_views.xml',
        'views/stock_quant_views.xml',
        'views/purchase_order_views.xml',
        'views/stock_scrap_views.xml',
        'views/stock_scrap_select_wizard_views.xml',
        'views/account_move_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mh_picking/static/src/views/stock_scrap_list_view.js',
            'mh_picking/static/src/models/barcode_picking_model.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
