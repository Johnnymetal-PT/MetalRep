# -*- coding: utf-8 -*-
{
    'name': 'PG Sale -> Purchase/MRP Link',
    'version': '17.0.1.0.0',
    'summary': 'Stat buttons na sale.order para abrir as MOs geradas e as Compras de componentes ligadas, via procurement group + fallback por origin.',
    'depends': ['sale', 'purchase', 'purchase_stock', 'sale_stock', 'mrp'],
    'data': [
        'views/sale_order_views.xml',
    ],
    'description': """
PG Sale -> Purchase / MRP Link
==============================

a) Objetivo de negocio
----------------------
Permitir ao comercial, a partir da Sale Order, saltar diretamente
para:
- as Ordens de Producao (MOs) geradas pela SO;
- as Compras (POs) lancadas para os componentes dessas MOs.
Sem isto, o utilizador tem de procurar manualmente por ``origin``.

b) Pre-requisitos
-----------------
- Modulos standard ``sale``, ``purchase``, ``purchase_stock``,
  ``sale_stock``, ``mrp``.
- Fluxo MTO/MTO+Buy ativo, com ``procurement.group`` a ser criado em
  cada SO/MO (standard Odoo).

c) Como funciona
----------------
- Override de ``sale.order`` em ``models/sale_order.py``:
  - ``pg_purchase_order_count`` e ``pg_mrp_production_count``
    (computed, nao stored).
  - ``_pg_get_related_mos()``: une MOs por
    ``procurement_group_id == SO.procurement_group_id`` **e** MOs
    por ``origin == SO.name``. A uniao serve de seguranca porque na
    Piccolo cada MO ganha um procurement group proprio.
  - ``_pg_get_related_purchase_orders()``: a partir das MOs encontra
    POs por ``group_id in mo.procurement_group_id`` **e** por
    ``origin in mo.name``.
  - ``action_view_pg_related_purchase_orders()`` /
    ``action_view_pg_related_mos()``: devolvem act_window para
    abrir a lista filtrada.
- Override de ``mrp.production`` em ``models/mrp_production.py``:
  - Override de ``create()`` que, se a MO nao tem
    ``procurement_group_id`` mas tem ``origin``, vai buscar o
    ``procurement_group_id`` da SO correspondente e copia para a MO
    (``_pg_backfill_procurement_group_from_sale``).
  - Isto restaura a ligacao SO<->MO quando a MO foi criada por um
    fluxo que partiu o grupo (ex.: criacao manual).
- View XML: dois stat buttons no header da SO ligados as actions.

d) Passo a passo de utilizacao
------------------------------
1. Instalar o modulo.
2. Confirmar uma SO de produto MTO+Buy.
3. Abrir a SO: aparecem dois stat buttons:
   - "Ordens de Producao" (count de MOs)
   - "Compras Componentes" (count de POs)
4. Clicar abre uma lista filtrada dos respetivos documentos.

e) Exemplo pratico
------------------
SO ``S00789`` confirma "Cadeira X" (MTO). Odoo gera ``MO/00102`` que
por sua vez gera ``PO P00455`` para a "Espuma". Na SO aparece:
- "Ordens de Producao" = 1 (clica e abre MO/00102)
- "Compras Componentes" = 1 (clica e abre PO P00455)

f) FAQ / Resolucao de problemas
-------------------------------
- *"Contador a 0 e ha MO/PO obvias"* -> SO sem
  ``procurement_group_id`` E sem matches por ``origin``. Verificar se
  alguem mudou o nome da SO depois de confirmar.
- *"Aparece MO que nao deveria"* -> a uniao por ``origin`` pode
  apanhar MOs criadas manualmente com o mesmo nome no campo origin.
  Aceitar ou afinar o dominio se houver falsos positivos repetidos.

g) Pontos de atencao / avisos
-----------------------------
- O backfill em ``mrp.production.create`` corre para TODAS as MOs
  criadas. Penalidade desprezavel (1 search por MO sem grupo) mas
  manter em mente se houver bulk imports de MOs.
- Counts sao computed nao-stored (recalcula sempre que se abre a SO).
  Aceitavel pela cardinalidade. Para listas com milhares de SOs pode
  ser pesado se a view incluir os contadores em modo tree.
- Filtra ``state != 'cancel'`` nas MOs - alterado se for util incluir
  canceladas (ex.: para diagnostico).
""",
    'installable': True,
    'application': False,
}
