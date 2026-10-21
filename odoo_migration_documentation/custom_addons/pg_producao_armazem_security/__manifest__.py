# -*- coding: utf-8 -*-
{
    "name": "PG Producao/Armazem - Perfil de Seguranca",
    "summary": "Perfil de acesso para utilizador de Producao/Armazem: full "
               "Manufatura/ShopFloor/Inventario/Compras/Qualidade; Vendas so "
               "leitura com valores ocultos; BD Geral e Contabilidade ocultos.",
    "version": "18.0.1.0.0",
    "category": "Tools/Security",
    "author": "Parametro Global",
    "license": "LGPL-3",
    # Dependencias confirmadas contra vendor/odoo_src 17.0.
    "depends": [
        "base",
        "contacts",            # res.partner (leitura via base.group_user)
        "sale_management",     # Vendas (vista read-only + esconder montantes)
        "stock",               # Inventario
        "mrp",                 # Manufatura
        "mrp_workorder",       # Shop Floor
        "purchase",            # Compras
        "quality_control",     # Qualidade
    ],
    "data": [
        "security/pg_producao_armazem_groups.xml",
        "views/pg_producao_armazem_sale_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
