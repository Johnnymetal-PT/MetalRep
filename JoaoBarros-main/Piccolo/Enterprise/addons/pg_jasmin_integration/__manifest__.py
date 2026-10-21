# -*- coding: utf-8 -*-
{
    'name': 'PG JASMIN integração',
    'version': '17.0.1.0.0',
    'summary': 'PG JASMIN integração',
    'description': """
        Sincronização com JASMIN automático.
    """,
    'category': 'Accounting',

    'author': 'PG',
    'website': 'https://www.parametro.pt',

    'depends': ['point_of_sale','sale_stock', 'sale_management', 'account', 'sale_subscription'],

    'assets': {
        'point_of_sale._assets_pos': [
            'pg_jasmin_integration/static/src/**/*',
            #'pg_jasmin_integration/static/src/js/custom_action_pad.js',
        ],
        #'point_of_sale.assets': [
        #    'pg_jasmin_integration/static/src/js/custom_action_pad.js',
        #],
    },
    'data': [
        'views/account_move_views.xml',
        'views/res_config_settings_views.xml',
        'views/stock_move_views.xml',

    ],
    'installable': True,
    'application': False
}
