# -*- coding: utf-8 -*-
# =============================================================================
# MÓDULO OBSOLETO / DEPRECADO — NÃO USAR
# -----------------------------------------------------------------------------
# Versão antiga (17.0.1.0.0) da integração de faturação PHC, substituída pelo
# módulo `pg_phc_api_integration` (17.0.2.0.0), que acrescenta o suporte a
# guias de transporte (stock.picking). Mantida apenas por histórico.
# Não instalar nem alterar — usar `pg_phc_api_integration`.
# =============================================================================
{
    'name': '[OBSOLETO] pg PHC Api Integration',
    'version': '17.0.1.0.0',
    'summary': '[OBSOLETO — substituído por pg_phc_api_integration] PHC Api Integration',
    'description': """
        MÓDULO OBSOLETO / DEPRECADO.

        Versão antiga da integração de faturação PHC, substituída por
        `pg_phc_api_integration`. Mantida apenas por histórico.
        Não instalar nem desenvolver sobre este módulo.

        ---
        Allow to sync invoice in PHC Api automatically and manually.
        Task ID: 3724730
    """,
    'category': 'Accounting',

    'author': 'Odoo PS',
    'website': 'https://www.odoo.com',
    'license': 'LGPL-3',

    'depends': ['sale_stock', 'sale_management', 'pg_phc_api'],

    'data': [
        #'views/res_config_settings_views.xml',
        'views/account_move_views.xml',
    ],

    'installable': True,
    'application': False
}
