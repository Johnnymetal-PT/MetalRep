# -*- coding: utf-8 -*-
{
    "name": "PG MRP — Pronto preenche Quantidade",
    "version": "17.0.1.0.0",
    "depends": ["mrp"],
    "author": "Parametro Global",
    "category": "Manufacturing",
    "summary": "Ao marcar o componente como 'Pronto' (x_studio_pronto), "
               "preenche a Quantidade consumida (quantity) quando ha falta: "
               "com o 'Para Consumir' (should_consume_qty) se a WO esta em "
               "progresso, ou com a Procura/Demand (product_uom_qty) se a WO "
               "ainda esta confirmada.",
    "data": [],
    "description": """
PG MRP — Pronto preenche Quantidade
===================================

a) Objetivo
-----------
No controlo de material da MO, o operador marca cada componente como
"Pronto" (campo Studio ``x_studio_pronto``). Quando o faz, se ainda
houver quantidade por consumir nesse componente ("Para Consumir" >
"Quantidade"), o sistema preenche automaticamente a Quantidade consumida
(``quantity``) com o valor "Para Consumir" (``should_consume_qty``),
eliminando a falta.

b) Como funciona
----------------
- ``models/stock_move.py`` faz override de ``write``: quando o write
  coloca ``x_studio_pronto`` a True num movimento de materia-prima
  (``raw_material_production_id`` preenchido), calcula o alvo
  ``should_consume_qty or product_uom_qty`` (Para Consumir com a WO em
  progresso; Demand quando a WO ainda esta confirmada) e, se esse alvo
  for maior que ``quantity``, define ``quantity`` = alvo. Guarda
  anti-recursao (o segundo write so mexe em ``quantity``).

c) Pontos de atencao
--------------------
- So preenche quando ha falta (nunca reduz uma quantidade ja consumida).
- Nao mexe no campo ``picked`` ("Consumido"); se for preciso marcar
  tambem como consumido, e um passo adicional a decidir.
- ``x_studio_pronto`` e campo Studio: depende de existir na BD (como o
  report Listagem que tambem o usa).
""",
    "installable": True,
    "application": False,
}
