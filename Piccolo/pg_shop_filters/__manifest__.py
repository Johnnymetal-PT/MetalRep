# -*- coding: utf-8 -*-
{
    'name': 'PG Shop Filters',
    'version': '17.0.1.0.0',
    'summary': 'Botao "Mais Opcoes" no /shop que mostra/esconde em accordion os atributos de produto.',
    'category': 'Website',
    'author': 'Parametro Global',
    'depends': ['website', 'website_sale', 'web'],
    'data': [
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'pg_shop_filters/static/src/js/accordion.js',
            'pg_shop_filters/static/src/css/styles.css',
        ],
    },
    'description': """
PG Shop Filters
===============

a) Objetivo de negocio
----------------------
Em paginas /shop com muitos atributos (Tecido, Cor, Tamanho...) a
sidebar fica enorme e dificil de varrer. Este modulo esconde-a por
defeito e expoe um botao "Mais Opcoes" que abre/fecha o painel
inteiro - reduz a carga visual no primeiro contacto com a loja.

b) Pre-requisitos
-----------------
- Modulos standard ``website`` e ``website_sale``.
- Sidebar standard ``#wsale_products_attributes_collapse`` presente
  na vista do /shop (vem com ``website_sale.products``).

c) Como funciona
----------------
- ``views/templates.xml`` faz inherit de ``website_sale.products`` e:
  1. Injecta `<button id="toggleAttributesButton">Mais Opcoes</button>`
     antes do bloco de atributos.
  2. Forca ``style="display:none;"`` na div de atributos (esconde-a).
  3. Inclui o script ``static/src/js/accordion.js`` dentro do bloco.
- O JS expoe a funcao global ``toggleAttributes()`` chamada pelo
  ``onclick`` do botao, que mostra/esconde a div e alterna o
  simbolo + / -.

d) Passo a passo de utilizacao
------------------------------
1. Instalar o modulo.
2. Abrir /shop - a sidebar de atributos esta colapsada.
3. Clicar em "Mais Opcoes" para expandir.

e) Exemplo pratico
------------------
Loja com 12 atributos de tecido. No mobile a sidebar inteira ocupava
2 ecras de scroll; com o accordion, o cliente arranca no produto e
abre os filtros so se quiser.

f) FAQ / Resolucao de problemas
-------------------------------
- *"Botao nao faz nada"* -> verificar que o JS carrega
  (``/pg_shop_filters/static/src/js/accordion.js``). Se mudou o
  bundling de assets, refrescar com ``/web/refresh``.
- *"Sidebar nao fica escondida"* -> outra customizacao pode ter
  alterado o id ``wsale_products_attributes_collapse``. Reavaliar o
  ``xpath`` da template.

g) Pontos de atencao / avisos
-----------------------------
- Autor original do snippet: "Tone Biclas" (mantido por referencia).
- O modulo so adiciona o accordion na pagina ``website_sale.products``
  (lista). Em paginas de produto individual nao tem efeito.
- O script usa ``onclick="toggleAttributes()"`` inline em vez de
  ``addEventListener`` - precisa de funcao global. Se houver outro
  script global com o mesmo nome, colide.
""",
    'installable': True,
    'application': False,
}
