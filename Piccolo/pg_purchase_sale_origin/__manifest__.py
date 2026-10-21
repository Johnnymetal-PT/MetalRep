# -*- coding: utf-8 -*-
{
    "name": "PG Purchase — Venda de Origem",
    "version": "17.0.1.0.0",
    "depends": ["purchase_stock", "sale_mrp"],
    "author": "Parametro Global",
    "category": "Purchase",
    "summary": "Mostra no formulario da Compra a Fornecedor a Venda a Cliente "
               "que lhe deu origem, seguindo o circuito Venda -> Fabrico -> "
               "Compra pela cadeia de movimentos de stock.",
    "data": [
        "views/purchase_order_views.xml",
    ],
    "description": """
PG Purchase — Venda de Origem
=============================

a) Objetivo de negocio
----------------------
Na Piccolo o circuito e sempre Venda a Cliente -> Fabrico -> Compra a
Fornecedor. Standard, o formulario da Compra nao mostra a Venda que
esta na origem (com o Fabrico pelo meio, o campo "Documento de origem"
mostra a Ordem de Fabrico ou fica vazio). Este modulo adiciona um campo
``pg_sale_order_ids`` (e um botao inteligente) que liga a Compra a
Venda(s) a Cliente na origem.

b) Como funciona
----------------
Campo computado (nao armazenado) em ``purchase.order``:
- ``_pg_get_source_productions``: a partir das linhas da compra segue a
  cadeia de ``stock.move`` para jusante (``move_ids.move_dest_ids`` e
  ``order_line.move_dest_ids``) ate encontrar consumos de materia-prima
  de uma Ordem de Fabrico (``raw_material_production_id``). Percorre
  passos intermedios (fabrico multi-etapa) com um limite de seguranca.
- Das Ordens de Fabrico chega a Venda com a mesma expressao que o
  standard ``sale_mrp`` usa na MO:
  ``procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id``.

c) Pre-requisitos
-----------------
- ``purchase_stock`` (Compras + Stock) e ``sale_mrp`` (ponte Venda +
  Fabrico), que trazem ``procurement.group.sale_id`` e a ligacao MO->SO.
- Circuito real Venda -> Fabrico -> Compra assente em rotas standard
  (procurement). Compras criadas manualmente sem ligacao de procurement
  nao terao Venda de origem (comportamento esperado).

d) Pontos de atencao
--------------------
- Uma Compra agregada (merge de RFQ para o mesmo fornecedor) pode servir
  varias Ordens de Fabrico / Vendas: por isso o campo e ``Many2many``.
- Campo nao armazenado (recalculado ao abrir): nao e pesquisavel nem
  agrupavel. Se for preciso filtrar/agrupar por Venda, converter para
  armazenado e definir ``@api.depends`` da cadeia.
""",
    "installable": True,
    "application": False,
}
