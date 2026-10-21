# -*- coding: utf-8 -*-
# OBSOLETO - Nao usar este modulo em novas instalacoes.
# Substituido por: pg_bd_connection
#
# Diferenca face ao substituto:
#   - pg_bd_connection_old NAO inclui sincronizacao de stock.picking (guias).
#   - pg_bd_connection (atual) acrescenta integracao com stock e modelo
#     stock_picking.py para replicacao de movimentos de stock entre BDs.
#
# Mantido apenas por referencia historica. Marcar installable=False quando
# todas as instancias estiverem migradas para pg_bd_connection.
{
    "name": "PG BD Connection (OBSOLETO - usar pg_bd_connection)",
    "version": "1.0",
    "summary": "[OBSOLETO] Substituido por pg_bd_connection. Sync invoices between two Odoo databases.",
    "description": """
        OBSOLETO
        ========
        Este modulo foi substituido por **pg_bd_connection**, que e a versao
        atual e mantida.

        Substituto: ``pg_bd_connection``

        Diferencas principais:
        - pg_bd_connection acrescenta sincronizacao de ``stock.picking`` (guias),
          que este modulo nao tem.
        - pg_bd_connection inclui a dependencia ``stock`` no manifest.

        Nao instalar este modulo em ambientes novos. Migrar para
        pg_bd_connection.
    """,
    "author": "Parametro Global",
    "category": "Accounting",
    "depends": ["account", "sale", "account_reports", "web"],
    "data": [
        "views/account_move_view.xml",
        "views/report_ledger_highlight.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "pg_bd_connection/static/src/scss/account_report.scss",
        ],
        "account_reports.assets_pdf_export": [
            "pg_bd_connection/static/src/css/account_report_pdf.css",
        ],
    },
    "installable": True,
    "application": False,
}
