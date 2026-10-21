# -*- coding: utf-8 -*-
{
    "name": "PHC Connector",
    "version": "2.0.2",
    "summary": "Sync customers between Odoo and PHC CSWeb with required PHC fields",
    "author": "Parâmetro Global",
    "license": "LGPL-3",
    "depends": [
        "base",
        "account",
    ],
    "data": [
        "views/res_partner_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
}
