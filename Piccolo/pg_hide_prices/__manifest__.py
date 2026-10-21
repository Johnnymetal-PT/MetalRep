# -*- coding: utf-8 -*-
{
    'name': 'PG Hide Product Prices for Non-Logged Users',
    'version': '17.0.1.0.0',
    'summary': 'Esconde precos e CTAs de compra no /shop e na ficha de produto para utilizadores nao autenticados (publicos).',
    'author': 'Parametro Global',
    'category': 'Website',
    'depends': ['website_sale'],
    'data': [
        'views/website_templates.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'pg_hide_prices/static/src/css/hide_price.css',
        ],
    },
    'description': """
PG Hide Prices
==============

a) Objetivo de negocio
----------------------
A Piccolo trabalha B2B com precos negociados; precos nao devem
aparecer a anonimos. Este modulo esconde precos e CTAs (call-to-action
de compra) a quem nao esta autenticado, mantendo a navegacao do
catalogo aberta a publicos.

b) Pre-requisitos
-----------------
- Modulo standard ``website_sale``.
- Grupo standard ``base.group_user`` (qualquer interno) e
  ``base.group_public`` (publicos).
- Templates afetados: ``website_sale.product_price`` e
  ``website_sale.product`` (CTAs).

c) Como funciona
----------------
- ``views/website_templates.xml`` faz inherit de:
  - ``website_sale.product_price`` -> ao ``<span class="oe_price">``
    adiciona dinamicamente a classe ``hidden`` quando o utilizador
    nao pertence a ``base.group_user``.
  - ``website_sale.product`` -> mesma logica aplicada ao
    ``<div id="o_wsale_cta_wrapper">``.
- ``security/ir_rule.xml`` define uma ``ir.rule`` que permite a
  ``base.group_public`` ler anexos (``ir.attachment``) cujo
  ``res_model in ['product.template', 'product.product']`` (read-only).
  Isto e necessario para que publicos consigam ver fichas tecnicas
  e imagens de produto **sem** precisar de login.
- ``security/ir.model.access.csv`` complementa o acesso (read) a
  modelos relevantes.
- ``static/src/css/hide_price.css`` define a regra ``.hidden { ... }``.

d) Passo a passo de utilizacao
------------------------------
1. Instalar o modulo.
2. Em sessao anonima, abrir um produto - sem preco, sem botoes de
   compra. Ficha tecnica e fotos continuam visiveis.
3. Apos login (utilizador interno ou portal **interno**), precos
   reaparecem.

e) Exemplo pratico
------------------
Cliente publico abre "Cadeira X": ve fotos, descricao e fichas
tecnicas, mas o bloco do preco e o botao "Add to Cart" estao
ocultos. Apos login com utilizador interno os precos voltam.

f) FAQ / Resolucao de problemas
-------------------------------
- *"Cliente portal nao ve preco"* -> o teste e
  ``has_group('base.group_user')`` (utilizadores INTERNOS). Para
  mostrar a portais B2B, alterar para ``base.group_portal`` ou um
  grupo customizado. **Decisao consultiva**, nao alterar sem
  validar com o cliente.
- *"CTA reaparece"* -> outra customizacao pode estar a sobrepor a
  classe ``hidden``. Inspecionar via DevTools.

g) Pontos de atencao / avisos
-----------------------------
- O criterio e baseado em ``base.group_user`` (utilizadores
  internos). Clientes do portal B2B **nao** veem preco a menos que
  o grupo seja alterado.
- ``ir.rule`` para ``base.group_public`` da read a anexos de
  produto - perfil deliberado para publicos verem fichas. Reavaliar
  se o catalogo tiver fichas confidenciais.
- A regra `t-attf-class` injeta a classe condicionalmente; depende
  do CSS ``.hidden { display: none }`` carregar - se o asset
  ``hide_price.css`` falhar, o preco volta a aparecer.
""",
    'installable': True,
    'application': False,
}
