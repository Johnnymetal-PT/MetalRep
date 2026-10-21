{
    'name': 'PG B2B Discounts',
    'version': '1.0',
    'author': 'Parametro Global',
    'category': 'Sales',
    'summary': 'Niveis de desconto B2B por cliente fidelizado, com pricelist combinada e desconto auto nas SO.',
    'description': """
PG B2B Discounts
================

a) Objetivo de negocio
----------------------
Atribuir tiers de desconto a parceiros B2B fidelizados com base no total
gasto. Cada tier:
- Tem uma pricelist propria (Bronze/Silver/Gold/Diamond Tier).
- E combinado com a pricelist "Descontos" numa pricelist gerada por cliente
  ("Combined (<nome>)") que herda os items das duas.
- Acresce um desconto fixo % nas linhas das novas Sale Orders (apenas se o
  desconto da linha for 0).

Niveis:
- Bronze - 10% (gasto > 0)
- Silver - 15% (gasto >= 1500)
- Gold - 20% (gasto >= 5000)
- Diamond - 25% (gasto >= 15000)

Um cron diario reavalia os tiers para os parceiros com
`x_studio_fidelizado=True`.

b) Pre-requisitos
-----------------
- Modulos: `sale`, `account`.
- Pricelists com os nomes exatos: "Descontos", "Bronze Tier", "Silver Tier",
  "Gold Tier", "Diamond Tier".
- Campo Studio `x_studio_fidelizado` (Boolean) em `res.partner`.
- Privilegio de criar `product.pricelist` (o modulo cria a "Combined (<nome>)"
  por cliente).

c) Como funciona
----------------
- `models/res_partner_discount.py`:
  - `res.partner` ganha:
    - `x_total_spendings` (Float, computed e store) - total gasto em SO
      em estado `sale` ou `done`.
    - `x_discount_tier` (Selection) - "none/bronze/silver/gold/diamond".
    - One2many `sale_orders` para `sale.order.partner_id`.
  - `_compute_total_spendings`:
    - Se `x_studio_fidelizado=False`: reset (total=0, tier=none, pricelist
      volta a default da empresa).
    - Caso contrario: soma `amount_total` das SO em sale/done, escolhe tier
      pelos thresholds e, se mudou, chama `_assign_combined_pricelist`.
  - `_assign_combined_pricelist`:
    - Procura "Descontos" e a pricelist do tier.
    - Chama `_create_combined_pricelist` que cria/refresca uma pricelist
      "Combined (<nome do partner>)" copiando os items das duas.
    - Atribui essa pricelist ao parceiro.
  - `sale.order.create`:
    - Apos criar a SO, aplica o desconto do tier (10/15/20/25) em todas as
      linhas que tenham `discount == 0`.
- `data/pg_b2b_discount_cron.xml`: cron diario que faz
  `model.search([('x_studio_fidelizado','=',True)])._compute_total_spendings()`.

d) Passo a passo de utilizacao
------------------------------
1. Criar as 5 pricelists: "Descontos", "Bronze Tier", "Silver Tier",
   "Gold Tier", "Diamond Tier" com os items pretendidos.
2. Em cada parceiro B2B, ativar `x_studio_fidelizado = True`.
3. Esperar pelo cron diario ou correr manualmente.
4. Verificar que o parceiro tem agora:
   - `x_total_spendings` calculado;
   - `x_discount_tier` definido;
   - `property_product_pricelist` apontando para "Combined (<nome>)".
5. Criar uma nova SO para esse parceiro - as linhas ja recebem o desconto
   do tier.

e) Exemplo pratico
------------------
- Parceiro "ACME LDA", fidelizado, com SO em sale/done totalizando 6500 EUR.
- Cron calcula `x_total_spendings = 6500`, atribui tier Gold (20%) e cria
  "Combined (ACME LDA)" com items de "Descontos" + "Gold Tier".
- Nova SO para ACME LDA: cada linha (sem desconto manual) fica com
  `discount = 20%`.

f) FAQ / Resolucao de problemas
-------------------------------
- "Cliente fidelizado nao muda de pricelist":
  Confirmar que existe pricelist com o nome "Descontos" E "<Tier> Tier".
  Caso falte uma, o partner so fica com a do tier.
- "Desconto nao aparece na linha":
  O `_apply_tier_discount_if_empty` so escreve discount em linhas com
  `discount == 0` na criacao. Se a linha for adicionada depois, ou se ja
  tiver desconto, e ignorada.
- "Pricelist 'Combined' acumulou items duplicados":
  `_create_combined_pricelist` apaga os items existentes antes de copiar -
  isso e intencional. Se os items nao foram copiados, validar permissoes
  no `sudo` da pricelist origem.
- "Tier desce mas o cliente nao perde a pricelist":
  Cuidado: o reset so acontece se `x_studio_fidelizado = False`. Para
  remover o tier, desativar a flag.

g) Pontos de atencao
--------------------
- O nome das pricelists e hardcoded. Renomear partir a logica.
- "Combined (<nome>)" cria uma pricelist por cliente; em catalogos com muitos
  parceiros isto pode encher o catalogo. [PONTO POR VALIDAR] criterio de
  limpeza/recolha.
- `_apply_tier_discount_if_empty` corre apenas no `create`; SO importadas
  ou criadas via API que ja tragam linhas nao recebem o desconto retroativo.
- Convive com [[pg_descontos]] (tag/ribbon no produto a partir da pricelist
  "Descontos"). Sao complementares mas usam ambos a pricelist "Descontos".
    """,
    'depends': ['sale', 'account'],
    'data': [
        'data/pg_b2b_discount_cron.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
