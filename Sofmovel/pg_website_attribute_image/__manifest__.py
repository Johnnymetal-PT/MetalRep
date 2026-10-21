# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'PG Website Product Attribute Image',
    'summary': 'Imagens em valores de atributo (cor/textura) no shop (modulo de terceiros).',
    'description': """
PG Website Product Attribute Image (modulo de terceiros - Visionee)
====================================================================

a) Origem e estado no projeto Sofmovel
--------------------------------------
[FACTO OBSERVADO] modulo de terceiros (Visionee, licenca AGPL-3). Mantido
no repositorio porque permite mostrar imagem em vez de bola de cor nos
valores de atributo do shop (ex. amostras de tecido).

NAO alterar a logica interna do modulo. Patches devem ser feitos por cima
em modulo proprio.

b) Objetivo de negocio (resumo do fornecedor)
---------------------------------------------
Adicionar o campo `image` (Image) ao `product.attribute.value`. Quando o
atributo tem display_type adequado, o shop mostra a imagem em vez do
swatch de cor.

c) Pre-requisitos
-----------------
- Modulos: `website_sale`, `stock`, `sale_product_configurator`.
- Atributos com display_type que beneficie de imagem (ex. "color", "pills").

d) Como funciona (resumo)
-------------------------
- `models/product_attribute.py`:
  - `product.attribute.value.image` (Image, max_width/max_height = False -
    deixa o Odoo gerir limites).
- `templates/shop_product.xml`: template QWeb que renderiza a imagem no
  shop.
- `views/product_attribute_value_views.xml`: vista backoffice para fazer
  upload da imagem por valor.
- `static/src/xml/product.xml`: registado em `web.assets_backend`.

e) Passo a passo de utilizacao
------------------------------
1. Em `Vendas / Configuracao / Atributos`, abrir um atributo.
2. Em cada valor, fazer upload de imagem.
3. No shop, o widget de atributo mostra as imagens em vez de quadrados de
   cor.

f) FAQ / Resolucao de problemas
-------------------------------
- "Imagem nao aparece no shop":
  Verificar que o atributo tem display_type compativel; alguns
  display_types (ex. "select") ignoram a imagem por design.
- "Imagem fica esticada":
  Sao mostradas tal como sao carregadas; nao ha resize automatico. Subir
  imagens com proporcao adequada.

g) Pontos de atencao (Sofmovel)
-------------------------------
- AGPL-3: pode ser modificado, mas qualquer fork tem de manter licenca
  AGPL. Em caso de dependencia direta avaliar com legal.
- Convive com [[pg_website_hide_unavailable_variant]] (ambos tocam em
  `product.attribute.value` / `product.attribute`); a ordem de carga
  importa.
- O manifesto declara `license` duas vezes (OPL-1 e AGPL-3); a segunda
  declaracao prevalece (AGPL-3). [PONTO POR VALIDAR] alinhar.
    """,
    'version': '17.0.1.0',
    'category': 'Website',
    'author': 'Visionee',
    'depends': [
        'website_sale', 'stock', 'sale_product_configurator',
    ],
    'data': [
        'templates/shop_product.xml',
        'views/product_attribute_value_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pg_website_attribute_image/static/src/xml/product.xml',
        ],
    },
    'images': [
        'static/description/banner.gif',
    ],
    'price': 20,
    'currency': "EUR",
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
}
