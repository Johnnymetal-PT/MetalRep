{
    'name': 'PG Buy and Sell by m2',
    'version': '1.0',
    'author': 'Parametro Global',
    'category': 'Sales',
    'summary': 'Venda e compra por m2 com largura/comprimento em SO, PO e website (carpetes).',
    'description': """
PG Buy and Sell by m2
=====================

a) Objetivo de negocio
----------------------
Permitir vender e comprar produtos a metragem (m2) com dimensoes (largura x
comprimento), tipicamente para corte de carpete/alcatifa. Diferenca face a
[[pg_sale_by_square_meter]]:
- Usa os campos Studio `x_studio_largura` e `x_studio_comprimento` (em vez de
  `comprimento`/`largura`).
- Estende tambem a Encomenda de Compra (PO).
- Inclui controller para o carrinho do website.

[PONTO POR VALIDAR] Existem dois modulos no projeto a tratar de venda por m2.
Confirmar qual e o oficial em uso e arquivar/depreciar o outro:
- [[pg_sale_by_square_meter]] - aborda apenas sales, campos sem prefixo Studio.
- [[pg_buy_and_sell_by_m2]] - estende sales+purchase+website, usa campos Studio.

b) Pre-requisitos
-----------------
- Modulos: `base`, `product`, `sale`, `purchase`, `website`, `website_sale`.
- Campos Studio criados:
  - `x_studio_largura` (Float) em `product.template`, `sale.order.line`,
    `purchase.order.line`.
  - `x_studio_comprimento` (Float) em `product.template`, `sale.order.line`,
    `purchase.order.line`.
- Produto a vender em m2: unidade de medida (`uom_name`) tem de ser exatamente
  "m²" (string com simbolo).

c) Como funciona
----------------
- `models/L_e_C.py` (ficheiro com nome "L_e_C" - largura e comprimento):
  - Em `product.template`: ao mudar `uom_name` para "m²", semeia os campos com
    1.00 (default util para o carrinho do website).
  - Em `sale.order.line`:
    - Calcula `total_area = largura * comprimento * product_uom_qty` (so se a
      UoM for "m²").
    - Recalcula `price_unit` multiplicando a area pelo preco do pricelist.
    - No `onchange`/`write`, anexa ao `name` da linha um sufixo do tipo
      " - 2.50 x 1.80 m²".
    - `_prepare_purchase_order_line` grava `sale_line_id` na PO line.
  - Em `purchase.order.line`:
    - Tambem calcula `total_area`.
    - Em `create`, le o `name` da SO line, extrai largura e comprimento e
      multiplica pelo price_unit original (preco fornecedor por m2).
- `controllers/main.py`:
  - Endpoint `/shop/cart/update_custom` (POST). Recebe `product_id`,
    `x_studio_largura` e `x_studio_comprimento`, calcula a area, remove
    linhas existentes do mesmo produto e cria uma nova linha com
    `product_uom_qty = area` e `price_unit = min_price`.
- `views/template.xml` e `views/website_template.xml`: vistas para o backoffice
  e snippet/route do website.

d) Passo a passo de utilizacao
------------------------------
1. No produto, definir UoM como "m²".
2. No website / loja: o cliente introduz largura e comprimento, submete o
   formulario para `/shop/cart/update_custom` e a linha do carrinho fica com a
   area como quantidade e o preco unitario ajustado.
3. Em backoffice, ao adicionar/editar a linha da SO, preencher largura e
   comprimento. O `name` da linha passa a incluir " - L x C m²".
4. Ao gerar uma PO a partir da SO, a PO line herda o `name` e ajusta o
   price_unit por area.

e) Exemplo pratico
------------------
- Produto "Carpete X" - 25 EUR/m2, UoM "m²".
- SO line com largura 2.50, comprimento 1.80, qty 1. Area = 4.5 m2.
- O `name` fica "Carpete X - 2.50 x 1.80 m²" e price_unit = 4.5 * 25 = 112.5.
- Ao gerar a PO, a PO line tambem preenche `x_studio_largura`/
  `x_studio_comprimento` e ajusta price_unit usando os mesmos valores.

f) FAQ / Resolucao de problemas
-------------------------------
- "O preco nao muda quando preencho largura/comprimento":
  Confirmar que `product_uom.name == 'm²'` exatamente (com simbolo). Se for
  "M2" ou outra string, as dependencias do compute nao disparam.
- "A PO line nao herda largura/comprimento":
  O codigo le do `name` da sale line para extrair largura/comprimento. Se o
  sufixo da SO line for editado a mao, a extracao falha (loga warning).
- "Tenho duplicacao de linhas no carrinho":
  O controller faz `unlink` das linhas existentes desse produto antes de criar
  a nova. Se houver mais que uma combinacao por produto/cliente, ponto a
  validar.

g) Pontos de atencao
--------------------
- Ha sobreposicao funcional com [[pg_sale_by_square_meter]]. Em principio so um
  destes deve estar em uso por instalacao.
- Os campos sao Studio (`x_studio_...`); migracoes de versao podem partir o
  modulo se os campos Studio forem renomeados.
- O parsing do sufixo do `name` para extrair dimensoes na PO line e fragil:
  qualquer alteracao manual ao texto da linha de venda perde a informacao.

[FACTO OBSERVADO] depende de campos Studio + UoM "m²" exata.
[INFERENCIA] anterior ao [[pg_sale_by_square_meter]]; este ultimo e mais
seguro (calcula em campos proprios sem depender de Studio).
    """,
    'depends': ['base', 'product', 'sale', 'purchase', 'website', 'website_sale'],
    'data': [
        'views/template.xml',
        'views/website_template.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
