# -*- coding: utf-8 -*-
{
    "name": "PG Hide Unavailable Variants",
    "summary": "Modulo terceiro (ErpMstar) que esconde no /shop os valores de atributo que nao tenham variantes disponiveis, sem ter de configurar exclusoes manualmente.",
    "description": """
PG Hide Unavailable Variants (ErpMstar - terceiro)
==================================================

NOTA SOBRE ESTE MODULO
----------------------
- **Origem**: ErpMstar Solutions.
- **Licenca**: comercial (40 EUR).
- **Status no projeto Piccolo**: vendored; codigo do
  fornecedor.

a) Objetivo de negocio
----------------------
Quando um produto tem muitas variantes e algumas combinacoes
nao existem (ex.: "Cadeira X" em "Vermelho" foi descontinuada),
o /shop standard ainda mostra essa combinacao. Este modulo
esconde automaticamente os valores que nao tem variante
correspondente.

b) Pre-requisitos
-----------------
- Modulo standard ``website_sale_stock``.

c) Como funciona (resumo)
-------------------------
- Adiciona uma flag boolean (em
  ``product.template`` ou ``website.product``) que ativa a
  ocultacao.
- Asset JS frontend (``static/src/js/hide.js``) intercepta o
  rendering da pagina e remove os swatches/options que apontam
  para variantes sem stock ou sem combinacao valida.

d) Passo a passo de utilizacao
------------------------------
1. Instalar.
2. No produto, ativar a opcao "Hide Unavailable Variants"
   (segundo a vista do modulo).
3. /shop -> os valores de atributo sem variante disponivel
   ficam escondidos automaticamente.

e) Exemplo pratico
------------------
"Cadeira X" tem variantes Vermelho, Azul, Verde. Stock so
existe para Azul e Verde. /shop com este modulo: o swatch
"Vermelho" desaparece sem precisar de configurar exclusoes
manualmente.

f) FAQ / Resolucao de problemas
-------------------------------
- *"Variante ainda aparece"* -> JS nao carregou ou outro
  modulo override do template do shop. Inspecionar DOM.
- *"Variantes desaparecem todas"* -> stock zero em todas;
  ativar a flag so quando ha matriz de stock valida.

g) Pontos de atencao / avisos
-----------------------------
- **NAO editar codigo do modulo**. Em update, perdem-se.
- Combina com ``pg_website_attribute_image`` (imagens de
  swatches) - ambos manipulam o DOM da pagina de variante.
- Como esconde via JS, view source ainda mostra os swatches -
  nao e seguranca, e apenas UX. Para esconder de robots,
  usar exclusoes Odoo nativas.
""",
    "author": "ErpMstar Solutions",
    "category": "eCommerce",
    "version": "17.0.1.0.0",
    "depends": ["website_sale_stock"],
    "data": [
        "views/views.xml",
        "views/templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "pg_website_hide_unavailable_variant/static/src/js/hide.js",
        ],
    },
    "installable": True,
    "application": True,
    "images": ["static/description/banner.gif"],
    "price": 40,
    "currency": "EUR",
}
