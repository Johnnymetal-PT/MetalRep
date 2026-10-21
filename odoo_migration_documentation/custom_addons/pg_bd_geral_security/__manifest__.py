# -*- coding: utf-8 -*-
{
    "name": "PG BD Geral - Perfil de Seguranca (Vendas)",
    "summary": "Perfil de acesso restrito para o utilizador 'BD Geral User' "
               "(Vendas sem eliminar, leitura em Manufatura/Reparacoes/Qualidade/"
               "Inventario, Projeto sem eliminar, apps ocultas).",
    "version": "18.0.1.0.0",
    "category": "Tools/Security",
    "author": "Parametro Global",
    "license": "LGPL-3",
    # NOTA: dependencias confirmadas contra vendor/odoo_src 17.0.
    # 'pg_bd_geral' (a app custom "BD Geral") NAO esta neste repo; o seu nome
    # tecnico tem de ser confirmado na BD e adicionado aqui. PONTO POR VALIDAR.
    "depends": [
        "base",
        "sale_management",      # Vendas (sales_team.group_sale_salesman*)
        "contacts",             # res.partner
        "stock",                # Inventario / stock.quant / product
        "mrp",                  # mrp.production / mrp.workorder / mrp.bom
        "mrp_workorder",        # instrucoes de ordem de trabalho (Enterprise)
        "repair",               # repair.order
        "quality_control",      # quality.check / quality.point (Enterprise)
        "project",              # project.project / project.task
        "project_todo",         # To-Do
        "hr_expense",           # Despesas (re-gate do menu)
        "crm",                  # CRM (re-gate do menu)
        "documents",            # Documentos (Enterprise)
        "knowledge",            # Conhecimento (Enterprise)
        "spreadsheet_dashboard",  # Paineis / Dashboards
        # "pg_bd_geral",        # <-- TODO: app custom "BD Geral" (nome tecnico a confirmar)
    ],
    "data": [
        "security/pg_bd_geral_security_groups.xml",
        "security/ir.model.access.csv",
        "security/pg_bd_geral_security_rules.xml",
        "views/pg_bd_geral_menu_visibility.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
    "auto_install": False,
}
