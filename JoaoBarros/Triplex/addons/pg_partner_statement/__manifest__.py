{
    "name": "Extrato Simplificado de Clientes",
    "summary": "Relatório simples de faturação e dívida por cliente num intervalo de datas",
    "version": "17.0.1.0.0",
    "license": "LGPL-3",
    "author": "Parametro Global",
    "depends": ["account", "sale"],
    "data": [
        "security/ir.model.access.csv",
        "views/partner_statement_line_views.xml",
        "views/partner_statement_wizard_views.xml",
        "report/partner_statement_report.xml",
        "report/partner_statement_template.xml",
        "views/menu.xml",
    ],
    "installable": True,
    "application": False,
}
