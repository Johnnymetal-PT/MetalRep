# -*- coding: utf-8 -*-
{
    "name": "PG Stock Picking MRP Product",
    "version": "17.0.1.0.0",
    "summary": "Acrescenta ao Stock Picking o produto final que esta a ser produzido (MO associada) e a ordem de venda original.",
    "author": "Parametro Global",
    "category": "Inventory",
    "depends": ["stock", "mrp"],
    "data": ["views/templates.xml"],
    "description": """
PG Stock Picking MRP Product
============================

a) Objetivo de negocio
----------------------
No fluxo MRP, um Stock Picking de consumo (movimentos de componentes
para a producao) nao mostra de forma obvia qual e o produto final que
esta a ser fabricado nem qual a SO original. Este modulo acrescenta
dois campos auxiliares no Picking para mostrar essa informacao em
listas/filtros.

b) Pre-requisitos
-----------------
- Modulos standard ``stock`` e ``mrp`` instalados.
- ``stock.picking.group_id`` preenchido e a corresponder ao
  ``procurement_group_id`` de uma ``mrp.production``.

c) Como funciona
----------------
- Override de ``stock.picking`` em ``models/main.py``:
  - ``manufactured_product_id`` (Many2one product.product) - o produto
    da MO ligada ao mesmo procurement group.
  - ``manufacturing_origin`` (Char) - o ``origin`` da MO (que tipicamente
    e o nome da SO).
  - Ambos com ``store=True`` e ``@api.depends('group_id')``.
- Para cada picking, faz ``self.env['mrp.production'].search(
  [('procurement_group_id', '=', picking.group_id.id)], limit=1)``
  e copia ``product_id`` e ``origin`` da MO encontrada.

d) Passo a passo de utilizacao
------------------------------
1. Instalar o modulo.
2. Abrir um Picking de consumo gerado por uma MO.
3. Ver os campos "Produto da Producao" e "Ordem de Venda" preenchidos.
4. Filtrar/agrupar pickings por estes campos em listas.

e) Exemplo pratico
------------------
MO/00088 fabrica "Cadeira Y" e origina o picking WH/MO/00088. Antes,
o picking so dizia "WH/MO/00088"; agora a lista mostra "Cadeira Y"
em "Produto da Producao" e "S00120" em "Ordem de Venda".

f) FAQ / Resolucao de problemas
-------------------------------
- *"Campo vazio"* -> o picking nao tem ``group_id`` ou nao ha MO com
  esse procurement group. Validar no debug menu o ``group_id`` do
  picking e procurar a MO com ``procurement_group_id`` correspondente.
- *"Performance"* -> o computed faz 1 search por picking. Para imports
  em massa pode ser pesado; considerar processar em batch.

g) Pontos de atencao / avisos
-----------------------------
- Os logs ``_logger.info("Checking Stock Picking ID: %s", ...)`` foram
  deixados para diagnostico. Sao verbose; silenciar via logger config
  em producao.
- Nomes em PT (``Produto da Producao``, ``Ordem de Venda``)
  propositadamente para refletir UI traduzida na Piccolo.
""",
    "installable": True,
    "auto_install": False,
    "application": False,
}
