# -*- coding: utf-8 -*-
{
    "name": "PG Cubicagem Wizard",
    "version": "17.0.3.0.0",
    "depends": ["stock"],
    "author": "Parametro Global",
    "category": "Inventory",
    "summary": "Wizard popup para introduzir ate 6 dimensoes (CxAxL) por stock.move, calcular cubicagem e peso e escrever em x_studio_volumes_3 / x_studio_peso_kg_1 / x_studio_cubicagem_1. Os inputs sao guardados por Entrega no stock.move (pg_cubicagem_inputs) para persistir entre aberturas; NAO sao propagados ao produto. Pre-preenche a partir do produto apenas quando a Entrega ainda nao tem inputs proprios.",
    "data": [
        # "views/stock_picking_views.xml",  # vista comentada - so esta ligada via stock_move_wizard
        "views/stock_move_wizard_views.xml",
        "security/ir.model.access.csv",
    ],
    "description": """
PG Cubicagem Wizard
===================

a) Objetivo de negocio
----------------------
Permitir ao operador da expedicao calcular cubicagem total (m3) e
peso (Kg) de um stock.move introduzindo ate 6 conjuntos
"Comprimento x Altura x Largura" - tipico de cargas com varios
volumes diferentes (ex.: caixotes A, B, C). O resultado e gravado em
campos Studio do move, que depois alimentam guias e relatorios.

b) Pre-requisitos
-----------------
- Modulo standard ``stock``.
- Campos Studio existentes em ``stock.move``:
  - ``x_studio_volumes_3`` (Integer) - n.o de caixas/volumes;
  - ``x_studio_peso_kg_1`` (Float) - peso total em Kg;
  - ``x_studio_cubicagem_1`` (Float) - cubicagem total em m3.
- Botao "Cubicagem" no formulario do ``stock.move`` (vista Studio /
  vista herdada externa - este modulo nao adiciona o botao).

c) Como funciona
----------------
- ``stock.move.cubicagem.wizard`` (TransientModel em
  ``models/stock_move_wizard.py``):
  - Campos: ``volumes``, 6 trios ``comprimento_N/altura_N/largura_N``.
  - ``cubicagem`` (computed): soma dos 6 produtos
    C*A*L (assume unidades coerentes em metros, devolvendo m3).
  - ``peso_kg`` (computed): ``cubicagem * 80`` (densidade fixa por
    convencao da Piccolo - usar so quando o material e o tipico do
    fluxo; para outros materiais introduzir manualmente).
- ``open_cubicagem_wizard`` em ``stock.move`` (``models/stock_move.py``)
  abre o wizard em modal com ``default_move_id`` no contexto.
- ``pg_cubicagem_inputs`` em ``stock.move`` (JSON): guarda os inputs do
  wizard por Entrega, para reabrir a calculadora já preenchida sem tocar
  no produto.
- ``_pg_packing_target`` no wizard: usado só na leitura de fallback —
  escolhe o nível de onde pré-preencher: variante (``product.product``)
  quando esta já tem dados próprios (``x_studio_volumes_3`` > 0), senão
  template (``product.template``). Espelha a automação Studio "PG Packing
  List Totals".
- ``default_get`` no wizard: pré-preenche a partir dos inputs já
  guardados na Entrega (``pg_cubicagem_inputs``); só se a Entrega ainda
  não tiver inputs próprios é que lê do produto (fallback, só leitura).
- ``action_calculate`` no wizard:
  0. Guarda os inputs na Entrega (``move.pg_cubicagem_inputs``). NÃO
     grava no produto — as dimensões/volumes do produto não são
     alteradas por este wizard.
  1. Le ``move.product_uom_qty``.
  2. ``required_boxes = ceil(qty * volume_per_unit)`` (mais ou menos -
     ver "Pontos de atencao" para a formula exata).
  3. ``total_peso = peso_per_unit * qty``,
     ``total_cubicagem = cubicagem_per_unit * qty``.
  4. ``move.write({'x_studio_volumes_3': ..., 'x_studio_peso_kg_1': ...,
     'x_studio_cubicagem_1': ...})``.

d) Passo a passo de utilizacao
------------------------------
1. Instalar o modulo.
2. Abrir um picking, expandir um stock.move.
3. Clicar no botao "Cubicagem" (vista Studio).
4. No popup, introduzir o numero de "Volumes" e as dimensoes dos
   caixotes representativos.
5. Confirmar - os campos ``x_studio_volumes_3``, ``x_studio_peso_kg_1``
   e ``x_studio_cubicagem_1`` do move ficam preenchidos.

e) Exemplo pratico
------------------
Move com ``product_uom_qty = 5``, dois tipos de caixotes:
- Caixote A: 1.2 x 0.6 x 0.4 = 0.288 m3
- Caixote B: 0.5 x 0.5 x 0.5 = 0.125 m3
Cubicagem por unidade = 0.413 m3 -> peso = 33.04 Kg.
Para qty=5 -> ``total_cubicagem = 2.065``, ``total_peso = 165.2 Kg``.

f) FAQ / Resolucao de problemas
-------------------------------
- *"Botao Cubicagem nao aparece"* -> o botao e definido em Studio;
  validar que a vista Studio do ``stock.move`` tem o botao a invocar
  ``open_cubicagem_wizard``.
- *"Peso calcula valor estranho"* -> a formula assume densidade fixa
  de 80 (Kg/m3); para outros materiais editar manualmente o campo
  apos o calculo.
- *"Volumes calculados a 0"* -> introduzir um valor em "Volumes"
  (campo ``volumes`` no wizard) > 0.

g) Pontos de atencao / avisos
-----------------------------
- A formula de ``required_boxes`` ``qty / (1 / volume_per_unit)``
  e equivalente a ``qty * volume_per_unit``; arredonda para cima se
  o resto for > 0. **Manter este comportamento se houver relatorios
  externos a contar com este arredondamento.**
- Campos ``x_studio_*`` sao Studio: o modulo depende destes existirem
  na BD. Em ambiente novo, validar primeiro a presenca dos campos.
- ``cubicagem`` e ``peso_kg`` no wizard sao ``store=False`` (computed
  on-the-fly) - so persistem nos campos do move depois de
  ``action_calculate``.
- Existe ``views/stock_picking_views.xml`` no manifest comentado;
  ficou de uma versao anterior. Nao remover sem confirmar.
""",
    "installable": True,
    "application": False,
}
