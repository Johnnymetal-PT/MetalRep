# -*- coding: utf-8 -*-
# Parâmetro Global - Cliente Domus & Acrópoles (Kyka)
{
    "name": "PG Kyka - Correções em relatórios (GT e ATCUD)",
    "author": "Parâmetro Global",
    "website": "https://parametro.global",
    "version": "18.0.1.0.0",
    "license": "LGPL-3",
    "category": "Inventory",
    "summary": "Guia de transporte com a morada de faturação no cabeçalho e QR/ATCUD "
               "deslocado para não tapar a numeração (tarefa 8195).",
    "depends": ["ptplus", "ptplus_stock"],
    "data": [
        "views/report_deliveryslip.xml",
        "views/report_atcud.xml",
    ],
    "installable": True,
    "application": False,
}
