# -*- coding: utf-8 -*-
# =============================================================================
# MÓDULO OBSOLETO / DEPRECADO — NÃO USAR
# -----------------------------------------------------------------------------
# Esta é uma cópia antiga do conector PHC, substituída pelo módulo `pg_phc_api`.
# É mantida apenas por histórico; o código ativo e mantido vive em `pg_phc_api`.
# Não instalar nem alterar este módulo — usar `pg_phc_api`.
# =============================================================================
{
    "name": "[OBSOLETO] PHC Connector",
    "version": "2.0.2",
    "summary": "[OBSOLETO — substituído por pg_phc_api] Sync customers between Odoo and PHC CSWeb",
    "description": """
        MÓDULO OBSOLETO / DEPRECADO.

        Cópia antiga do conector PHC, substituída pelo módulo `pg_phc_api`.
        Mantida apenas por histórico. Não instalar nem desenvolver sobre este
        módulo: o conector ativo e mantido é o `pg_phc_api`.
    """,
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
