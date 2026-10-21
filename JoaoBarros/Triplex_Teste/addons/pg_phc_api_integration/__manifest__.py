# -*- coding: utf-8 -*-
{
    'name': 'pg PHC Api Integration',
    'version': '17.0.1.0.0',
    'summary': 'PHC Api Integration',
    'description': """
        Allow to sync invoice in PHC Api automatically and manually.
        Task ID: 3724730
    """,
    'category': 'Accounting',

    'author': 'Odoo PS',
    'website': 'https://www.odoo.com',
    'license': 'LGPL-3',

    'depends': ['sale_stock', 'sale_management', 'pg_phc_api', 'account_reports'],

    'data': [
        #'views/res_config_settings_views.xml',
        'views/account_move_views.xml',
        'views/stock_picking_views.xml',
    ],

    'installable': True,
    'application': False
}
