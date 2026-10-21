{
    'name': 'PG Volume In Shipping',
    'version': '2.0',
    'author': 'Parametro Global',
    'category': 'Inventory',
    'summary': 'Quantidade de volumes, peso total e peso por volume nos documentos de stock e relatorios.',
    'description': """
PG Volume In Shipping
=====================

a) Objetivo de negocio
----------------------
Mostrar e calcular, nos pickings e respetivos relatorios de delivery slip, o
volume total, peso total e numero de volumes por linha e por picking. Para
artigos vendidos em multiplas embalagens (ex. sofa em 3 caixas), grava ainda
o peso de cada volume separado por "/" (ex. "12.5 / 18 / 9").

Tambem garante a propagacao do `default_code` / `barcode` do template para os
campos Studio das variantes (`x_studio_referncia_interna` /
`x_studio_cdigo_de_barras`).

b) Pre-requisitos
-----------------
- Modulos: `base`, `product`, `stock`.
- Campo `volume` em `product.product` (standard Odoo).
- Campos Studio `x_studio_referncia_interna` e `x_studio_cdigo_de_barras` em
  `product.product`.

c) Como funciona
----------------
- `models/product_volume_template.py`:
  - Adiciona em `product.template`:
    - `volume_qty` (Float, store) - quantidade de volumes que compoem o
      artigo.
    - `peso_cada_volume` (Char, default '0.0') - peso de cada volume
      separado por '/'.
  - `_onchange_propagate_to_variants`: quando muda `default_code` ou
    `barcode` no template, escreve nas variantes os campos Studio.
  - Em `product.product`: re-declara os campos Studio
    `x_studio_referncia_interna` e `x_studio_cdigo_de_barras` como
    `store=True`, `index=True` (para acelerar pesquisas).
- `models/account_volumes.py` (nome historico - o modelo nao tem que ver com
  account):
  - Em `stock.picking`:
    - `total_volume_by_qty` (m3), `total_weight_by_qty` (kg) e
      `total_volume_qty_by_qty` (numero de volumes) calculados a partir
      das moves.
    - `peso_cada_volume` related da move (so leitura).
  - Em `stock.move`:
    - `product_volume`, `product_weight`, `product_volume_qty` (related ao
      produto).
    - `product_volume_by_qty`, `product_weight_by_qty`,
      `product_volume_qty_by_qty` (calculados como
      `product_uom_qty * <valor unitario>`).
    - `peso_cada_volume` (related ao template via produto).
  - Em `stock.move.line`:
    - `peso_cada_volume` related da move.
    - Override de `_get_aggregated_product_quantities` para incluir nas
      linhas agregadas listas com volumes/pesos por linha - usadas nos
      relatorios.
- `views/product_volume_view.xml` / `qweb_report.xml` / `report/...`: adicionam
  os campos as vistas e ao delivery slip.

d) Passo a passo de utilizacao
------------------------------
1. No produto:
   - Preencher `volume_qty` (ex. 3 se o produto vier em 3 caixas).
   - Preencher `peso_cada_volume` (ex. "12.5/18/9").
   - Preencher `weight` e `volume` no produto standard (peso e volume
     totais por unidade).
2. Criar e validar um picking de delivery.
3. Imprimir o delivery slip: ja mostra volumes totais, peso total e
   numero de volumes.

e) Exemplo pratico
------------------
- Produto "Sofa 3 Lugares":
  - `weight` = 39.5 (kg)
  - `volume` = 0.45 (m3)
  - `volume_qty` = 3
  - `peso_cada_volume` = "12.5 / 18 / 9"
- Move com 2 sofas:
  - `product_weight_by_qty` = 2 * 39.5 = 79
  - `product_volume_by_qty` = 2 * 0.45 = 0.9
  - `product_volume_qty_by_qty` = 2 * 3 = 6
- Picking totals: 0.9 m3, 79 kg, 6 volumes.

f) FAQ / Resolucao de problemas
-------------------------------
- "Volumes/pesos nao aparecem no slip":
  Confirmar que o produto tem `weight` e `volume` preenchidos. Sem eles os
  campos `_by_qty` ficam a 0.
- "peso_cada_volume sai sempre como '0.0'":
  E o default. Para mostrar valor real, atualizar o template.
- "Variante nao tem referencia Studio":
  O `_onchange_propagate_to_variants` propaga a partir do template em
  `onchange`. Para variantes criadas anteriormente, e preciso disparar de
  novo (gravar o template depois de uma alteracao trivia em default_code
  ou barcode).
- "Total dos volumes no picking nao bate":
  O calculo soma as moves do `move_ids_without_package`. Se houver pacotes
  ja embalados, valores podem divergir; rever a logica caso o cliente use
  packages.

g) Pontos de atencao
--------------------
- Nome do ficheiro `account_volumes.py` e historico (o codigo nao toca em
  account). [PONTO POR VALIDAR] renomear sem partir importacoes.
- `peso_cada_volume` e Char com formato livre; o consumidor (este modulo e
  os imports Kave/Sofmovel) usam o separador "/". Manter a convencao.
- O modulo define indices em `x_studio_referncia_interna` /
  `x_studio_cdigo_de_barras` (Studio); util em catalogos grandes.
    """,
    'depends': ['base', 'product', 'stock'],
    'data': [
        'views/product_volume_view.xml',
        'views/qweb_report.xml',
        'report/report_deliveryslip_template.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
