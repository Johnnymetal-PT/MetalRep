# -*- coding: utf-8 -*-
{
    'name': 'pg Planeamento Oficina',
    'version': '17.0.1.0.0',
    'summary': 'Painel de planeamento da oficina (CEO/Administração)',
    'description': """
        Painel CEO/Administração para acompanhamento em tempo real de:
        - Encomendas (sale.order.line) e respetivas ordens de produção
        - Estado de componentes por fornecedor (tecido, casco, inox, polidor, embalagem)
        - Fornecedores com encomendas pendentes
        - Previsão de faturação por semana

        Substitui o ficheiro Planeamento_Oficinna22.xlsx, mantendo todos os
        campos sincronizados em tempo real com sale.order, mrp.production e
        os respetivos componentes BOM.
    """,
    'category': 'Manufacturing',
    'author': 'Parametro Global',
    'license': 'LGPL-3',

    'depends': ['sale_management', 'sale_stock', 'mrp', 'account'],

    'data': [
        'security/pg_planeamento_security.xml',
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/pg_planeamento_views.xml',
        'views/pg_planeamento_menus.xml',
    ],

    'post_init_hook': '_post_init_backfill',

    'installable': True,
    'application': True,
}
