{
    'name': 'PG Descontos',
    'version': '1.0',
    'author': 'Parametro Global',
    'category': 'Sales',
    'summary': 'Aplica tag "Desconto" e ribbon 5 aos produtos da pricelist "Descontos" (cron diario).',
    'description': """
PG Descontos
============

a) Objetivo de negocio
----------------------
Marcar visualmente no website e no backoffice os produtos que estao em
campanha de desconto. A logica:
- Produtos na pricelist "Descontos" (match por nome ilike "Desconto") ficam
  com a tag "Desconto" e ribbon ID 5.
- Produtos com `compare_list_price > list_price` (preco antes do desconto
  superior ao preco atual) tambem ficam com a tag/ribbon.
- O campo `compare_list_price` e sincronizado automaticamente com o campo
  Studio `x_studio_preo_antes_desconto`, para que o badge "X%" no website
  reflita o valor de "antes".

E corrido por cron diario.

b) Pre-requisitos
-----------------
- Modulos: `product`, `sale`.
- Pricelist com nome contendo "Desconto" (ex. "Descontos").
- Ribbon de website com ID 5 (ex. "Promo"). [Hardcoded.]
- Campo Studio `x_studio_preo_antes_desconto` em `product.template`.

c) Como funciona
----------------
- `models/product_pricelist_discount.py` adiciona `apply_discount_tag` em
  `product.template`:
  1. Procura a pricelist "Desconto*"; se nao existir, faz log warning e sai.
  2. Garante a tag `product.tag` "Desconto" (cria se faltar).
  3. Sincroniza `compare_list_price = x_studio_preo_antes_desconto` em TODOS
     os produtos (sudo).
  4. Procura todos os produtos com tag "Desconto" OU `website_ribbon_id == 5`
     e remove-os caso nao satisfacam as condicoes (nao estao na pricelist e
     nao tem `compare_list_price > list_price`).
  5. Aplica tag + ribbon aos produtos da pricelist.
  6. Aplica tag + ribbon aos produtos com `compare_list_price > list_price`.
- `data/pg_descontos_cron.xml` define o cron diario que chama
  `model.apply_discount_tag()`.

d) Passo a passo de utilizacao
------------------------------
1. Criar a pricelist "Descontos" e os respetivos `product.pricelist.item`.
2. Confirmar que o ribbon ID 5 existe (vista `Configuracao / Ribbons`).
3. Para produtos com preco "antes" diferente, preencher
   `x_studio_preo_antes_desconto`.
4. Esperar pela proxima execucao do cron (1 dia) ou correr manualmente:
   `model.apply_discount_tag()` em `Tecnicas / Cron / "Apply Desconto Tag"`.
5. Validar que os produtos da pricelist aparecem com tag "Desconto" e
   ribbon ativo no website.

e) Exemplo pratico
------------------
- Produto X com list_price = 199 EUR, x_studio_preo_antes_desconto = 249.
- Apos cron: compare_list_price = 249, tag "Desconto", ribbon ID 5.
- No website mostra "-20%" automaticamente.

f) FAQ / Resolucao de problemas
-------------------------------
- "Pricelist 'Descontos' nao encontrada":
  Log warning e nada acontece. Criar pricelist e correr de novo.
- "Produtos certos sem tag":
  Verificar se `pricelist_item.product_tmpl_id` (ou
  `pricelist_item.product_id.product_tmpl_id`) esta preenchido; o cron
  considera ambos.
- "Tag fica em produtos que nao deviam":
  O cron remove a tag quando o produto nao esta na pricelist E o
  `compare_list_price` nao e maior. Se ambos forem verdade (esta na
  pricelist OU preco antes maior), a tag fica.

g) Pontos de atencao
--------------------
- Ribbon ID 5 esta hardcoded. Migracoes precisam atualizar.
- O cron percorre TODOS os produtos (`self.sudo().search([])`) para
  sincronizar `compare_list_price`; em catalogos grandes esta operacao e
  pesada.
- A logica corre completa em cada execucao - nao usa cache nem delta.
- Convive com [[pg_b2b_discounts]]: este aplica tags no produto, o outro
  cria pricelists combinadas por cliente. Sao funcoes complementares.
    """,
    'depends': ['product', 'sale'],
    'data': [
        'data/pg_descontos_cron.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
