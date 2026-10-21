{
    'name': 'MH Inventário',
    'version': '18.0.1.2.0',
    'category': 'Inventory',
    'author': 'Make It Happen, SA',
    'website': 'https://makeithappen.co.mz/pt',
    'summary': 'Gestão personalizada de Inventário criado pela Make It Happen.',
    'description': """
    Módulo de Inventário personalizado criado pela empresa Make It Happen, permitindo controle mais eficiente e detalhado de estoque.
    """,
    'depends': ['mh_base', 'product', 'stock', 'stock_account', 'purchase', 'sale_stock'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/product_family_views.xml',
        'views/business_segment_views.xml',
        'views/product_template_views.xml',
        'views/product_product_views.xml',
        'views/product_search_views.xml',
        'views/product_attribute_views.xml',
        'views/res_config_settings_views.xml',
        'views/stock_picking_views.xml',
        'views/menus_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
