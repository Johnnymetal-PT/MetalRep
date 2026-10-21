{
    "name": "PG Update Variant Prices",
    "version": "17.0.1.0.0",
    "author": "Parametro Global",
    "category": "Sales",
    "license": "LGPL-3",
    "summary": "Recalcula o preco unitario das variantes a partir das regras da pricelist (preenche x_variant_sale_price).",
    "description": """
PG Update Variant Prices
========================

a) Objetivo de negocio
----------------------
Em pricelists que tem regras especificas por variante (`applied_on =
'0_product_variant'`), grava o preco resultante num campo proprio da variante
(`x_variant_sale_price`), para uso em listagens, relatorios ou integracoes
que precisem do "preco oficial da pricelist" sem ter de re-correr o
`_get_product_price` a cada leitura.

NOTA: a accao e disparada manualmente em cada pricelist; nao tem cron
associado. O campo `x_variant_sale_price` nao substitui `lst_price`; o
codigo apenas escreve nele e mantem o `lst_price` intocado.

b) Pre-requisitos
-----------------
- Modulo standard `product`.
- Pricelists com items ao nivel da variante (`applied_on='0_product_variant'`).

c) Como funciona
----------------
- `models/product_pricelist.py`:
  - `product.product` ganha `x_variant_sale_price` (Float).
  - Em `product.pricelist`:
    - `action_update_variant_prices`: itera pelos items da pricelist com
      `applied_on='0_product_variant'`, calcula o preco com
      `pricelist._get_product_price(product=variant, quantity=1.0,
      partner=None)` e escreve no `x_variant_sale_price` da variante (so
      se diferente do `lst_price` actual).
    - Loga progresso por variante.

d) Passo a passo de utilizacao
------------------------------
1. Configurar a pricelist com items por variante.
2. Abrir a pricelist; chamar `action_update_variant_prices` (via botao
   em vista ou Programmer Mode -> Execute method).
3. Verificar nas variantes o campo `x_variant_sale_price`.

e) Exemplo pratico
------------------
- Pricelist "Pro" com items por variante:
  - "Cadeira Vermelha" -> 89 EUR
  - "Cadeira Azul" -> 92 EUR
- Apos accao:
  - Variante Cadeira Vermelha: `x_variant_sale_price = 89`.
  - Variante Cadeira Azul: `x_variant_sale_price = 92`.

f) FAQ / Resolucao de problemas
-------------------------------
- "Variante nao actualizou":
  Confirmar que o item da pricelist tem `applied_on = '0_product_variant'`
  e `product_id` preenchido. Itens ao nivel de template ou categoria nao
  sao considerados.
- "Erro ao calcular preco":
  O log mostra a excecao por variante; pode ser items ambiguos ou regras
  com partner_id obrigatorio. O codigo passa `partner=None`.
- "O `lst_price` da variante nao mudou":
  E intencional. O modulo escreve apenas no campo custom
  `x_variant_sale_price`.

g) Pontos de atencao
--------------------
- A logica e `_logger.info` por variante; pricelists com muitos items geram
  muitos logs. Em producao considerar baixar verbosity ou agrupar.
- Sem cron associado: tem de ser disparado a mao apos cada alteracao
  significativa na pricelist.
- O campo `x_variant_sale_price` esta declarado em `product.product`; o
  consumo cabe a outras vistas/relatorios.
    """,
    "depends": ["product"],
    "installable": True,
    "application": False
}
