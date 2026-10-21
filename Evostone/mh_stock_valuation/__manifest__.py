# -*- coding: utf-8 -*-
{
    'name': 'MH Stock Valuation - PCMP',
    'version': '18.0.1.2.0',
    'category': 'Inventory/Inventory',
    'summary': 'Compatibilidade histórica PCMP e valorização AVCO standard',
    'description': """
MH Stock Valuation - PCMP
=========================

Adiciona um novo método de custeio ao Odoo 18: **PCMP (Preço de Custo Médio Ponderado)**
com contexto de ano fiscal.

Funcionalidades:
----------------
* Novo método de custeio: PCMP (Ano Fiscal)
* Ponto de partida por ano fiscal para cada produto
* Cálculo automático do PCMP a cada entrada de stock
* Transição automática entre anos fiscais
* Campo próprio pcmp_price (não usa standard_price)
* Grupos de Lote (base.lot.group) para valorização PCMP por lote
* Grupos de Preço (lot.price.group) para gestão de preços por dimensões
* Campo lot_name na linha de compra para criar/associar grupos de lote
* Suporte a Custos Adicionais (Landed Costs) para PCMP
* Stock Inicial - documento para entrada de stock inicial com valorização
* Hierarquia de preços: base.lot.group → lot.price.group → stock.lot

Fórmula PCMP:
-------------
    numerator = initial_value - sales_value + import_value
    denominator = initial_stock - sales_qty + import_qty
    new_pcmp = numerator / denominator

Comportamento:
--------------
* ENTRADAS: Recalcula pcmp_price automaticamente
* SAÍDAS: Usa pcmp_price existente (não recalcula)
* TRANSIÇÃO: Wizard para copiar PCMP do ano anterior

Configuração:
-------------
1. Ir a Inventário > Configuração > Categorias de Produtos
2. Selecionar método de custeio: "PCMP (Ano Fiscal)"
3. Configurar valorização: Manual ou Automática

Autor: MH
    """,
    'author': 'MH',
    'website': '',
    'depends': [
        'mh_inventory',  # Define product_form usado em base.lot.group
        'stock_account',
        'purchase_stock',  # Necessário para override de _prepare_stock_move_vals
        'stock_landed_costs',  # Suporte a custos adicionais para PCMP
        'mail',  # Necessário para mail.thread em base.lot.group e lot.price.group
        'sale',  # Necessário para menus de venda
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/stock_picking_type_data.xml',
        'views/mh_pcmp_fiscal_year_views.xml',
        'views/mh_pcmp_wizard_views.xml',
        'views/product_views.xml',
        'views/base_lot_group_views.xml',
        'views/lot_price_group_views.xml',
        'views/stock_picking_views.xml',
        'views/stock_move_line_snapshot_views.xml',
        'views/stock_valuation_layer_views.xml',
        'views/stone_stock_views.xml',
        'views/stock_lot_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
