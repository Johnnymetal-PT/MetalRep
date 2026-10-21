# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "PG Website Product Attribute Image",
    "summary": "Modulo terceiro (Visionee, AGPL-3) que permite associar imagens aos valores de atributo (product.attribute.value.image_1920); estas imagens substituem os swatches de cor no /shop.",
    "version": "17.0.1.0",
    "category": "Website",
    "author": "Visionee",
    "license": "AGPL-3",
    "depends": [
        "website_sale", "stock", "sale_product_configurator",
    ],
    "data": [
        "templates/shop_product.xml",
        "views/product_attribute_value_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "pg_website_attribute_image/static/src/xml/product.xml",
        ],
    },
    "description": """
PG Website Attribute Image (Visionee - terceiro)
================================================

NOTA SOBRE ESTE MODULO
----------------------
- **Origem**: Visionee.
- **Licenca**: AGPL-3 (livre, mas obriga a partilhar mods).
  *Em manifest ha tanto "OPL-1" como "AGPL-3" - a Visionee
  duplicou a chave; a final (AGPL-3) prevalece.*
- **Status no projeto Piccolo**: vendored; codigo do
  fornecedor.

a) Objetivo de negocio
----------------------
No /shop, em vez de mostrar nomes ou swatches de cor genericos
para as variantes de atributo, mostrar uma **imagem real** do
material (foto da textura do tecido, da cor do verniz, etc.).

b) Pre-requisitos
-----------------
- Modulos standard ``website_sale``, ``stock`` e
  ``sale_product_configurator``.

c) Como funciona (resumo)
-------------------------
- Acrescenta ``image_1920`` em ``product.attribute.value``.
- Template QWeb ``templates/shop_product.xml`` faz inherit e
  substitui o picker standard pelo set de imagens.
- Assets backend (``views/product.xml`` em XML, para Owl)
  acrescentam o widget de upload de imagem no formulario.

d) Passo a passo de utilizacao
------------------------------
1. Instalar.
2. Backoffice > Atributos de Produto > abrir cada valor (ex.:
   "Linho Bege").
3. Upload imagem (foto da textura).
4. /shop > pagina do produto que use esse atributo -> picker
   passa a usar a imagem.

e) Exemplo pratico
------------------
Atributo "TECIDO" com valores "Linho Bege", "Linho Castanho",
"Veludo Verde" - cada um com foto da textura. Cliente no /shop
ve os tres swatches como fotos reais em vez de squares de cor.

f) FAQ / Resolucao de problemas
-------------------------------
- *"Picker continua com swatches"* -> a categoria do atributo
  e ``select`` em vez de ``color``/``radio``. Validar
  ``product.attribute.display_type``.
- *"Imagem cortada"* -> o widget frontend cropa para quadrado;
  preparar imagens 1:1 antes do upload.

g) Pontos de atencao / avisos
-----------------------------
- **NAO editar codigo do modulo**.
- Pode colidir com outros modulos que renderizam o picker
  custom (ex.: ``pg_shop_filters`` accordion). Validar
  interaccao visual.
- Combinacao com ``pg_product_variant_description_bytesfuel``:
  ambos manipulam o DOM da pagina de variante - ordem de
  carregamento pode causar visual flicker.
""",
    "images": [
        "static/description/banner.gif",
    ],
    "price": 20,
    "currency": "EUR",
    "installable": True,
    "auto_install": False,
}
