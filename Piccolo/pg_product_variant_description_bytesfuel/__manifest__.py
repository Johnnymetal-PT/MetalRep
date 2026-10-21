# -*- coding: utf-8 -*-
{
    "name": "PG Website Product Variant Description",
    "version": "17.0.1.0",
    "author": "Bytesfuel",
    "website": "https://bytesfuel.com/",
    "category": "eCommerce",
    "summary": "Modulo terceiro (Bytesfuel, OPL-1) que adiciona um campo de descricao por variante (product.product.description_variant) visivel na ficha do produto do website quando o cliente escolhe variantes.",
    "description": """
PG Product Variant Description (Bytesfuel - terceiro)
=====================================================

NOTA SOBRE ESTE MODULO
----------------------
- **Origem**: Bytesfuel (`https://bytesfuel.com/`).
- **Licenca**: OPL-1 (paga - 10 USD).
- **Status no projeto Piccolo**: vendored - codigo do
  fornecedor; manter sem edicoes.

a) Objetivo de negocio
----------------------
Mostrar no /shop uma descricao especifica de cada variante
quando o cliente seleciona atributos. Em vez de uma descricao
generica do template, cada combinacao pode ter texto proprio
(materiais, certificacoes, advertencias).

b) Pre-requisitos
-----------------
- Modulo standard ``website_sale``.
- Licenca paga ativa.

c) Como funciona (resumo)
-------------------------
- Acrescenta campo ``description`` (ou similar) em
  ``product.product`` - editavel na ficha da variante.
- Asset JS frontend (``static/src/js/mixin.js``) intercepta
  a mudanca de variante no /shop e re-injeta a descricao.
- Template ``views/templates.xml`` define o placeholder onde
  o JS escreve.

d) Passo a passo de utilizacao
------------------------------
1. Instalar.
2. Abrir variante no backoffice -> preencher descricao
   especifica.
3. /shop -> selecionar essa variante -> ver descricao a mudar
   automaticamente.

e) Exemplo pratico
------------------
"Cadeira X" com variantes "Linho Bege" e "Linho Castanho".
- Variante Linho Bege: descricao "Tecido natural, acabamento
  matte".
- Variante Linho Castanho: descricao "Tecido natural, tom mais
  escuro, indicado para ambientes amplos".
No /shop, alternar entre variantes muda o texto sem reload.

f) FAQ / Resolucao de problemas
-------------------------------
- *"Descricao nao muda"* -> JS nao carregou (verificar
  ``/pg_product_variant_description_bytesfuel/static/src/js/mixin.js``
  no asset bundle).
- *"Descricao em branco"* -> a variante nao tem texto
  preenchido; falls back ao template.

g) Pontos de atencao / avisos
-----------------------------
- **NAO editar codigo do modulo**. Atualizacoes perdem
  alteracoes locais.
- O mixin JS pode colidir com outras customizacoes que
  alteram o evento de mudanca de variante (ex.:
  ``pg_website_attribute_image``). Validar interaccao.
""",
    "depends": ["website_sale"],
    "data": [
        "views/templates.xml",
        "views/product_variant_view.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "/pg_product_variant_description_bytesfuel/static/src/js/mixin.js",
        ],
    },
    "images": ["static/description/banner.png"],
    "installable": True,
    "application": True,
    "license": "OPL-1",
    "price": 10.00,
    "currency": "USD",
}
