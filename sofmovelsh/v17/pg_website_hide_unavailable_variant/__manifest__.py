# -*- coding: utf-8 -*-
{
    'name': "PG Hide Unavailable Variants",
    'summary': "Esconde no website variantes esgotadas ou marcadas como `hide_on_website` (modulo de terceiros).",
    'description': """
PG Hide Unavailable Variants (modulo de terceiros - ErpMstar Solutions)
=======================================================================

a) Origem e estado no projeto Sofmovel
--------------------------------------
[FACTO OBSERVADO] modulo de terceiros (ErpMstar Solutions, licenca paga,
preco upstream 40 EUR). Mantido no repositorio porque suporta a logica de
esconder variantes indisponiveis no website Sofmovel.

NAO alterar a logica interna - patches devem ser feitos em modulo proprio
por cima para nao bloquear futuros upgrades.

b) Objetivo de negocio (resumo do fornecedor)
---------------------------------------------
Marcar variantes (em `product.product`) como "hide_on_website=True". Essas
variantes deixam de aparecer no shop, sem precisar definir "Exclusions" na
configuracao de atributos. Em `product.attribute` ganha um selector
`unavailable_value_view_type` (None / Hide) que determina como mostrar os
valores indisponiveis no widget de atributos do website.

c) Pre-requisitos
-----------------
- Modulo standard `website_sale_stock` instalado.
- Licenca do modulo upstream valida (se aplicavel).

d) Como funciona (resumo)
-------------------------
- `models/models.py`:
  - `product.template.get_variant_count`: devolve um dicionario com info
    sobre variantes validas/invisible, valores por atributo e mapeamento
    de child items - consumido pelo JS frontend.
  - `product.template._get_first_possible_combination`: filtra
    combinacoes cujo `product.product.hide_on_website=True` para que a
    primeira combinacao seleccionada seja realmente visivel.
  - `product.template._is_combination_possible`: respeita o flag
    `hide_on_website` apenas quando chamado com contexto especial.
  - `product.attribute.unavailable_value_view_type` (Selection none/hide).
  - `product.product.hide_on_website` (Boolean).
- `controllers/controllers.py`:
  - Rota `/get_product_variant_data_website` (JSON-RPC, publica) que
    devolve `get_variant_count` para um template.
- `static/src/js/hide.js`: oculta visualmente os valores de atributo no
  shop.

e) Passo a passo de utilizacao (resumo)
---------------------------------------
1. Em `product.attribute`, escolher `unavailable_value_view_type = 'hide'`.
2. Em variantes especificas, marcar `hide_on_website = True`.
3. Recarregar a sessao do website; valores indisponiveis ficam ocultos.

f) FAQ / Resolucao de problemas
-------------------------------
- "Variante continua a aparecer":
  Verificar se `hide_on_website` esta True na variante, e se
  `unavailable_value_view_type` esta em "hide" no atributo correspondente.
- "Combinacao default e ainda assim invisivel":
  O override de `_get_first_possible_combination` ja salta combinacoes
  hidden; se ainda assim ficar, validar se nao ha cache HTTP.

g) Pontos de atencao (Sofmovel)
-------------------------------
- Modulo proprietario. Manter o codigo upstream sem patches diretos.
- O override de `_is_combination_possible` so se aplica quando o contexto
  tem `special_call`; outros usos do metodo nao sao afetados.
- Convive com [[pg_website_attribute_image]] (que tambem extende
  `product.attribute.value` para imagens) - validar ordem de carga em caso
  de conflito.
    """,
    'author': "ErpMstar Solutions",
    'category': 'eCommerce',
    'version': '1.0',
    'depends': ['website_sale_stock'],
    'data': [
        'views/views.xml',
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'pg_website_hide_unavailable_variant/static/src/js/hide.js',
        ]
    },
    'installable': True,
    'application': True,
    'images': ['static/description/banner.gif'],
    'price': 40,
    'currency': 'EUR',
}
