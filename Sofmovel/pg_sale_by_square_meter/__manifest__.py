{
    'name': 'PG Sale by Square Meter',
    'version': '17.0.1.0.0',
    'author': 'Parametro Global',
    'category': 'Sales',
    'summary': 'Venda por m2 em linhas de encomenda introduzindo comprimento e largura.',
    'description': """
PG Sale by Square Meter
=======================

a) Objetivo de negocio
----------------------
Permitir vender produtos cortados a medida (por exemplo carpetes, alcatifas, tecidos)
introduzindo nas linhas de encomenda comprimento e largura em metros. A area
calculada substitui automaticamente a quantidade vendida (product_uom_qty), para que
o preco e os impostos sejam ja calculados pela area real cortada.

b) Pre-requisitos
-----------------
- Modulo standard `sale` instalado.
- Os produtos a vender por m2 devem ter o preco unitario configurado por m2.
- Nao requer configuracao Studio adicional.

c) Como funciona
----------------
- Heranca de `sale.order.line` (ver `models/sale_order_line.py`):
  - Adiciona os campos `comprimento` (m), `largura` (m) e `area` (m2 stored e
    computado).
  - O metodo `_compute_area` recalcula a area sempre que muda comprimento ou largura.
  - O metodo `_sync_product_qty_from_dimensions` propaga a area para
    `product_uom_qty`, usando `skip_square_meter_qty_sync` no contexto para nao
    voltar a entrar em loop.
  - `_onchange_square_meter_dimensions` mantem o sync ao editar a linha no UI.
  - `create` e `write` sao sobrecarregados para garantir o sync mesmo em criacao
    programatica ou em writes que toquem em dimensoes.
  - `_compute_amount` foi reescrito para usar `product_uom_qty` (ja sincronizado)
    e disparar o recalculo de `tax_totals` na sale order pai.
- Heranca em `views/sale_order_line_views.xml`:
  - Insere os campos `comprimento`, `largura` e `area` no tree da
    `sale.view_order_line_tree` e no tree embutido no form da sale order.

d) Passo a passo de utilizacao
------------------------------
1. Criar/abrir uma Encomenda de Venda.
2. Adicionar uma linha com o produto a cortar.
3. Preencher Comprimento (m) e Largura (m) na linha.
4. Confirmar que a coluna `Area (m2)` foi calculada e que a coluna `Quantidade`
   passou a ser igual a area.
5. Os totais (subtotal, IVA, total) da linha sao recalculados automaticamente.

e) Exemplo pratico
------------------
- Carpete vendida a 25 EUR/m2.
- Linha: Comprimento 2,5 m; Largura 1,8 m.
- O modulo grava area = 4,5 m2 e ajusta product_uom_qty para 4,5.
- Subtotal = 4,5 x 25 = 112,5 EUR.

f) FAQ / Resolucao de problemas
-------------------------------
- "Coloquei comprimento e largura mas o subtotal nao mexe":
  Verificar se a UoM da linha tem rounding compativel; o sync usa
  `float_compare` com o rounding da UoM e so escreve se houver diferenca real.
- "A quantidade volta a 0 ao guardar":
  Confirmar que a chave de contexto `skip_square_meter_qty_sync` nao esta a ser
  forcada por outro modulo. Ela so deve ser True durante o proprio sync interno.
- "Quero forcar uma quantidade manual diferente da area":
  Hoje o sync escreve sempre que ambas as dimensoes sao > 0. Se for necessario,
  abrir ponto de validacao porque a regra de negocio atual e que dimensoes
  preenchidas mandam sobre a quantidade manual.

g) Pontos de atencao
--------------------
- O metodo `_compute_amount` faz `_compute_tax_totals` no `sale.order` pai para
  garantir que os totais ficam consistentes; isto introduz I/O adicional e pode
  pesar em encomendas com muitas linhas.
- A area so e calculada quando comprimento > 0 e largura > 0; caso contrario o
  campo fica a 0 e o sync e ignorado.

[FACTO OBSERVADO] modulo implementado e dependente apenas de `sale`.
[PONTO POR VALIDAR] sobreposicao funcional com [[pg_buy_and_sell_by_m2]], que
usa campos `x_studio_largura` / `x_studio_comprimento`. Confirmar qual e a
solucao oficialmente em uso antes de novas alteracoes.
    """,
    'depends': ['sale'],
    'data': [
        'views/sale_order_line_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
