# -*- coding: utf-8 -*-

{
    'name': 'PG Imagens em Valores de Atributo',
    'version': '1.0',
    'category': 'Website',
    'summary': 'Adiciona imagens a valores de atributos e mostra-as na seleção de variantes.',
    'description': '''
Objetivo de negocio
===================
Melhora a escolha de variantes no website quando o nome do atributo não chega e o utilizador precisa de ver textura/cor/material.

Pre-requisitos
==============
Website/eCommerce instalado. Valores de atributo com imagem carregada. Nota: Odoo 19 já tem suporte nativo a imagens em atributos; validar se este addon ainda é necessário antes de evoluir.

Como funciona
=============
Herda `product.attribute.value` para garantir campo `image` e altera `website_sale.variants` para mostrar valores em carousel/modal de imagens.

Passo a passo de utilizacao
===========================
1. Abrir Atributos > Valores. 2. Carregar imagem no valor. 3. Abrir produto com esse atributo no website. 4. Selecionar variante pela imagem.

Exemplo pratico
===============
Atributo `Tecido` com valores `Linho` e `Veludo` mostra miniaturas para cada valor na página do produto.

FAQ / Resolucao de problemas
============================
Se a imagem não aparece, confirmar se o atributo usa display compatível e se o template herdado ainda bate com Odoo 19. Se houver conflito com o seletor nativo, avaliar remover este modulo.

Pontos de atencao / avisos
==========================
Possível sobreposição com funcionalidade standard Odoo 19 (`product.attribute.value.image` e display type `image`). Tratar como legado/adaptado até decisão funcional.
''',
    'author': 'Visionee, adaptado PG',
    'license': 'AGPL-3',
    'depends': ['website_sale', 'stock'],
    'data': ['templates/shop_product.xml', 'views/product_attribute_value_views.xml'],
    'assets': {'web.assets_backend': ['pg_website_attribute_image/static/src/xml/product.xml']},
    'images': ['static/description/banner.gif'],
    'price': 20,
    'currency': 'EUR',
    'installable': True,
    'application': False,
    'auto_install': False,
}
