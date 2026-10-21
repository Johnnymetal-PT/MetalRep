# -*- coding: utf-8 -*-
{
    "name": "PG Shop Floor — Nº de Encomenda",
    "version": "17.0.1.0.0",
    "depends": ["mrp_workorder"],
    "author": "Parametro Global",
    "category": "Manufacturing",
    "summary": "Mostra o Nº de Encomenda (mrp.production.origin) e a "
               "Referencia do Cliente (sale.order.client_order_ref via cadeia "
               "sale_mrp) no topo dos cartoes do Shop Floor, e coloca o Nº de "
               "Encomenda como primeiro metodo de pesquisa. Circuito Piccolo: "
               "Venda -> Fabrico, onde 'origin' da MO e o nome da encomenda.",
    "data": [
        "views/mrp_production_search_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "pg_mrp_shopfloor_encomenda/static/src/**/*.js",
            "pg_mrp_shopfloor_encomenda/static/src/**/*.xml",
        ],
    },
    "description": """
PG Shop Floor — Nº de Encomenda
===============================

a) Objetivo
-----------
No Shop Floor (mrp_workorder, Enterprise), mostrar em cada cartao (Ordem
de Producao ou Ordem de Trabalho) o **Nº de Encomenda** de origem, no
topo, e permitir pesquisar por esse numero como primeiro metodo.

b) Base factual
---------------
No Piccolo o circuito e Venda -> Fabrico. Confirmado por API que o campo
``mrp.production.origin`` contem o nome da encomenda (ex.: ``ENC01623``),
igual a venda de origem obtida via grupo de aprovisionamento (sale_mrp).
Por isso usa-se ``origin`` (simples e alinhado com o que o Shop Floor ja
mostra como "Origem"), em vez de recomputar a cadeia sale_mrp no
frontend.

c) Como funciona
----------------
- ``models/mrp_production.py``: campo computado ``pg_client_order_ref``
  que segue a cadeia sale_mrp ate a venda de origem e devolve o
  ``client_order_ref`` (Referencia do Cliente).
- ``static/src/mrp_display_encomenda.js``:
  - patch de ``MrpDisplayAction.fieldsStructure`` para carregar o campo
    ``origin`` da ``mrp.production`` no Shop Floor;
  - patch de ``MrpDisplayRecord`` com o getter ``pgEncomenda`` (le de
    ``props.production`` para cartoes de OT, ou do proprio registo para
    cartoes de OP).
- ``static/src/mrp_display_record.xml``: herda o template
  ``mrp_workorder.MrpDisplayRecord`` e adiciona a linha do Nº de
  Encomenda no topo do cabecalho do cartao.
- ``views/mrp_production_search_view.xml``: herda
  ``mrp.view_mrp_production_filter`` (search view partilhada da
  ``mrp.production``): renomeia o campo ``origin`` para "Nº de Encomenda"
  e move-o para primeiro. NOTA: por ser a search view partilhada, a
  alteracao aplica-se tambem a lista normal de Ordens de Producao
  (decisao validada com o cliente).

d) Pontos de atencao
--------------------
- Customizacao de frontend Enterprise (patch de componentes OWL +
  heranca de template): revalidar apos upgrades do Odoo/mrp_workorder.
- MOs sem venda de origem (fabrico manual/stock) podem ter ``origin``
  vazio; nesse caso a linha simplesmente nao aparece.
""",
    "installable": True,
    "application": False,
}
