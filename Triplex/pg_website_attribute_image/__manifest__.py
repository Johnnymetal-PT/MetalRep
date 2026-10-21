# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'PG Website Product Attribute Image',
    'summary': 'Imagem por valor de atributo (ex.: amostras de cor/tecido) na loja online',
    'description': """
PG Website Product Attribute Image
==================================

Origem
------
Módulo de terceiros (Visionee). Esta é a versão ATIVA; existem cópias antigas em
`pg_website_attribute_image_old` e `_oldold` que NÃO devem ser usadas.

Objetivo de negócio
-------------------
Mostrar uma imagem em cada valor de atributo (por exemplo, a amostra real da cor ou do
tecido) na página de produto da loja, tornando a escolha de variantes mais visual.

Pré-requisitos
--------------
- Módulos: `website_sale`, `stock`, `sale_product_configurator`.
- O atributo cujos valores levam imagem deve ser do tipo "radio" (ver README).

Como funciona
-------------
- `product.attribute.value`: acrescenta o campo `image` (a amostra a mostrar), mais
  `has_image` (booleano guardado) e `image_url` (URL público já redimensionado, com
  chave de cache). O `product.template.attribute.value` expõe os dois por `related`.
- Templates/JS: a imagem é apresentada na ficha de produto da loja (templates/shop_product.xml)
  e no backend (static/src/js, static/src/xml). Em ambos é servida **por URL**, com
  `loading="lazy"` — nunca embutida em base64 no HTML.
- `ir.http._dispatch` (otimização): na resposta de `/sale_product_configurator/get_values`,
  substitui os blobs de imagem por booleanos (`_strip_images`), evitando enviar imagens
  pesadas no payload do configurador (carrega-se a imagem por URL quando necessário).

Porque a amostra vai por URL e não em base64
--------------------------------------------
Até à versão 17.0.2.0 a ficha de produto embutia cada amostra em base64. Num produto
com 102 tecidos isso dava uma página de 33 MB, com o último grupo de atributos a
aparecer só a 99,7 % do documento. Até o browser lá chegar, o `website_sale` enviava
uma combinação de variante incompleta, o Odoo dava-a como impossível e o carrossel
ficava com `css_not_available` (`opacity: 0.2`): a imagem do produto aparecia esbatida
sem motivo aparente. Servida por URL, a mesma página fica abaixo de 1 MB e a amostra
é partilhada em cache por todo o catálogo.

Passo a passo de utilização
---------------------------
1. Ir a Inventário > Configuração > Atributos.
2. No atributo (tipo "radio"), abrir cada valor e carregar a imagem (amostra).
3. Publicar o produto; na loja, os valores do atributo passam a mostrar as imagens.

Exemplo prático
---------------
Atributo "Tecido" com valores "Linho Bege", "Veludo Verde": carregar em cada valor a foto
do tecido; o cliente, na página do sofá, vê as amostras e escolhe visualmente.

FAQ / Resolução de problemas
----------------------------
- P: As imagens não aparecem na loja.
  R: Confirmar que o atributo é do tipo "radio" e que cada valor tem imagem carregada.
- P: O configurador estava lento com imagens grandes.
  R: É precisamente o que o override do ir.http resolve (não envia o blob, só indica que existe).
- P: Qual versão usar? Há vários módulos parecidos.
  R: Usar ESTE (`pg_website_attribute_image`); os `_old`/`_oldold` estão obsoletos.

Pontos de atenção
-----------------
- Módulo de origem externa (Visionee), adquirido e mantido internamente.
- O override de `ir.http._dispatch` depende do endpoint do configurador standard.
- Nunca voltar a embutir a amostra em base64 no template da loja: é o que provocava
  a ficha de produto de 33 MB e a imagem esbatida (ver secção acima).
""",
    'version': '17.0.2.0',
    'category': 'Website',
    'author': 'Visionee',
    'license': 'OPL-1',
    'depends': [
        'website_sale', 'stock', 'sale_product_configurator',
    ],
    'data': [
        'templates/shop_product.xml',
        'views/product_attribute_value_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'pg_website_attribute_image/static/src/css/website_attribute_image.css',
        ],
        'web.assets_backend': [
            'pg_website_attribute_image/static/src/js/ptav_image_backend.js',
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

