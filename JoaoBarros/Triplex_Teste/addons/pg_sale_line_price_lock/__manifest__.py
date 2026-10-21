# -*- coding: utf-8 -*-
{
    "name": "PG Sale Line Price Lock",
    "version": "17.0.1.0.0",
    "summary": "Preco unitario das linhas de venda em so leitura por utilizador",
    "category": "Sales",
    "author": "Parametro Global",
    "license": "LGPL-3",
    "depends": ["sale_management"],
    "data": [
        "security/sale_line_price_security.xml",
        "views/sale_order_views.xml",
    ],
    "installable": True,
    "application": False,
}
