{
    'name': 'MH Stock At Date',
    'summary': 'Relatório interactivo de quantidades em stock à data, por localização e lote',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',
    'author': 'Stone Trading',
    'depends': ['stock', 'stock_account', 'stock_enterprise'],
    'data': [
        'security/security.xml',
        'data/client_action.xml',
        'reports/stock_at_date_templates.xml',
        'data/report_action.xml',
        'views/stock_quant_views.xml',
        'views/stock_menus.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mh_stock_at_date/static/src/js/stock_at_date.js',
            'mh_stock_at_date/static/src/js/stock_at_date.xml',
        ],
    },
    'installable': True,
    'application': False,
}
