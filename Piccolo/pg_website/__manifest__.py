# -*- coding: utf-8 -*-
{
    'name': 'PG Website',
    'version': '17.0.1.0.0',
    'category': 'Website',
    'summary': 'Homepage custom (/HomePage), menu dinamico e campos auxiliares de imagem para o website da Piccolo.',
    'author': 'Parametro Global, SA',
    'website': 'http://www.parametro.pt',
    'depends': ['base', 'product', 'website', 'website_sale'],
    'data': [
        'views/templates.xml',
        'views/website_menu.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'pg_essani_website/static/src/css/custom_homepage.css',
        ],
    },
    'description': """
PG Website
==========

a) Objetivo de negocio
----------------------
Concentrar customizacoes do website da Piccolo - homepage propria
("/HomePage"), menu dinamico ("/dynamic_menu") e helpers de imagem em
``product.template`` / ``product.image`` para alimentar templates QWeb.

b) Pre-requisitos
-----------------
- Modulos standard ``website``, ``website_sale``, ``product``.
- Categoria publica ``product.public.category`` com nome **literal**
  "Todas" no topo - o controlador ``/HomePage`` procura essa
  categoria por ``name == 'Todas'``. Sem esta categoria a homepage
  carrega sem child categories.

c) Como funciona
----------------
- ``controllers/home_page.py``:
  - ``/HomePage`` (auth=public, website=True): procura categoria
    "Todas" e renderiza ``pg_website.homepage_test`` com a lista
    ``child_categories``.
  - ``/dynamic_menu``: renderiza ``pg_website.dynamic_menu_template``
    (template definido em ``views/templates.xml``).
- ``models/product_template.py``:
  - ``extra_image_ids`` (One2many product.image) - exposicao de
    imagens extra do produto.
  - ``main_image`` (Binary, computed a partir de ``image_1920``) -
    espelho para uso em QWeb sem ter de tratar fallback.
- ``models/product_image.py``:
  - ``image_base64`` (Char, computed) - serializa ``image_1920`` em
    base64 utf-8 para templates que precisem da string crua.
- ``views/templates.xml`` define a homepage custom e o menu dinamico.
- ``views/website_menu.xml`` cria a entrada de menu para a homepage.
- Assets carregam CSS de ``pg_essani_website`` (referencia historica
  do tema base reaproveitado - ver "Pontos de atencao").

d) Passo a passo de utilizacao
------------------------------
1. Instalar o modulo.
2. Backoffice > eCommerce > Categorias do Website > criar/garantir
   categoria com nome ``Todas`` no topo, com sub-categorias filhas.
3. Aceder a ``/HomePage`` - mostra cards das child categories.
4. Aceder a ``/dynamic_menu`` para validar o template do menu.
5. No template QWeb dos produtos, usar ``product.main_image`` ou
   ``product.extra_image_ids`` para mostrar imagens.

e) Exemplo pratico
------------------
Categoria "Todas" com filhos "Tecidos", "Cadeiras", "Mesas". Em
``/HomePage`` aparecem 3 cards a apontar para cada subcategoria.
A imagem usada e ``main_image`` (computed = ``image_1920``).

f) FAQ / Resolucao de problemas
-------------------------------
- *"/HomePage vazia"* -> nao existe categoria publica chamada
  ``Todas`` (atencao a capitalizacao). Logs do controller indicam
  "Todas category not found".
- *"CSS nao aplica"* -> o asset aponta para
  ``pg_essani_website/static/src/css/custom_homepage.css`` (modulo
  externo). Se esse modulo nao estiver instalado, o CSS falha em
  silencio.
- *"Imagem extra nao aparece"* -> ``extra_image_ids`` so expoe os
  registos; o template QWeb tem de iterar e renderizar cada imagem.

g) Pontos de atencao / avisos
-----------------------------
- O asset CSS aponta para ``pg_essani_website`` (heranca de outro
  projeto). Se o ficheiro nao existir nessa pasta, o bundling deixa
  warning silencioso. Considerar mover o CSS para
  ``pg_website/static/src/css/custom_homepage.css`` em proxima
  iteracao - **nao** alterar sem confirmar onde o ficheiro vive de
  facto.
- ``image_base64`` em ``product.image`` esta ``store=True`` - vai
  inchar a BD se houver muitas imagens; reavaliar antes de imports
  massivos.
- Rota ``/HomePage`` com capital H - sensivel a case (Werkzeug case-
  sensitive em routing). Links externos tem de usar exatamente
  ``/HomePage``.
""",
    'installable': True,
    'application': False,
    'auto_install': False,
}
