# -*- coding: utf-8 -*-
# pg_categories_image/__manifest__.py
{
    'name': 'PG Category Images',
    'version': '17.0.1.0.0',
    'category': 'Website',
    'summary': 'Acrescenta dois campos de imagem extra a product.category para uso em paginas do website (categorias com animacao).',
    'author': 'Parametro Global',
    'depends': ['website_sale'],
    'data': [
        'views/product_category_views.xml',
    ],
    'description': """
PG Category Images
==================

a) Objetivo de negocio
----------------------
Permitir associar imagens adicionais a cada categoria de produto para
serem usadas no website (banners, animacoes hover, segundo plano).
Sem este modulo, ``product.category`` standard nao tem campos para
imagens extra alem do ``image_1920`` de ``product.public.category``.

b) Pre-requisitos
-----------------
- Modulo standard ``website_sale`` instalado.
- Templates QWeb do website que consumam os campos
  ``cat_image_1`` / ``cat_image_2`` (este modulo nao injecta os
  templates de frontend - so disponibiliza os campos no backoffice).

c) Como funciona
----------------
- Acrescenta dois campos ``Binary`` no modelo ``product.category``:
  - ``cat_image_1`` ("Imagem 1")
  - ``cat_image_2`` ("Imagem 2")
- Ambos com ``attachment=True`` (gravados em ``ir.attachment`` em vez
  de inline na tabela, para nao inchar pg_dump).
- A view ``views/product_category_views.xml`` mostra os campos no
  formulario de categoria.

d) Passo a passo de utilizacao
------------------------------
1. Instalar o modulo.
2. Inventario / Vendas > Configuracao > Categorias de Produto > abrir
   uma categoria.
3. Carregar "Imagem 1" e/ou "Imagem 2" no formulario.
4. No template do website, referenciar via
   ``t-att-src="image_data_uri(category.cat_image_1)"`` ou semelhante.

e) Exemplo pratico
------------------
Categoria "Tecidos > Linho": "Imagem 1" e a textura do tecido em
detalhe, "Imagem 2" e uma foto de ambiente. No /shop a homepage
mostra a Imagem 2; no hover passa a Imagem 1.

f) FAQ / Resolucao de problemas
-------------------------------
- *"Onde aparecem as imagens?"* -> este modulo so as armazena. Tem de
  haver templates QWeb a consumir os campos no website.
- *"Imagem nao aparece no site"* -> validar que o template usa
  ``cat_image_1`` (campo em ``product.category``) e nao confunde com
  ``image_1920`` de ``product.public.category`` (modelo diferente).

g) Pontos de atencao / avisos
-----------------------------
- O modulo esta sobre ``product.category`` (backoffice). Para o site
  ecommerce o standard usa ``product.public.category``. Se a Piccolo
  decidir migrar para imagens em ``product.public.category``, este
  modulo passa a redundante.
- ``application: True`` no manifest e enganador - nao e uma "app"
  topo de menu; mantemos por compatibilidade com a versao instalada.
""",
    'installable': True,
    'application': True,
    'auto_install': False,
}
