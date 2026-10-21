# -*- coding: utf-8 -*-

{
    'name': 'PG Website Essani',
    'version': '1.0',
    'category': 'Website',
    'summary': 'Personaliza homepage, categorias e imagens hover do website Essani.',
    'description': '''
Objetivo de negocio
===================
Adapta a experiência pública/extranet do website Essani para navegar por famílias e mostrar imagens alternativas de produto.

Pre-requisitos
==============
Website/eCommerce instalados. Categorias públicas organizadas sob `Todas`. Categorias internas com campos `cat_image_1` e `cat_image_2` (fornecidos por `pg_product_update`). Se visibilidade por cliente estiver ativa, requer `website_product_visibility`.

Como funciona
=============
Controller substitui a homepage e envia categorias visíveis. Templates substituem homepage, ajustam listagem de categorias, filmstrip e imagem do card de produto para mostrar imagem principal + primeira extra em hover.

Passo a passo de utilizacao
===========================
1. Configurar categorias e imagens. 2. Atualizar modulo. 3. Abrir `/` e validar famílias. 4. Abrir `/shop`/categoria e validar hover nos produtos.

Exemplo pratico
===============
Categoria `Cadeiras` tem `cat_image_1` e `cat_image_2`; na homepage aparece o cartão da categoria. Produto com imagem extra mostra segunda imagem no hover.

FAQ / Resolucao de problemas
============================
Se a homepage fica vazia, validar categoria `Todas` e regras de visibilidade. Se imagens de categoria falham, confirmar campos `cat_image_1/cat_image_2`. Se hover não aparece, confirmar `extra_image_ids` sem variante.

Pontos de atencao / avisos
==========================
Tem dependência funcional por nome da categoria `Todas` e por nomes de campos criados noutros módulos. Evitar duplicar lógica com `pg_web_attach_pdf_view.categories_page` sem alinhar ambos.
''',
    'author': 'Parametro Global, SA',
    'website': 'http://www.parametro.pt',
    'depends': ['base', 'product', 'website', 'website_sale'],
    'data': ['views/templates.xml', 'views/website_menu.xml'],
    'assets': {'web.assets_frontend': ['pg_website/static/src/css/custom_homepage.css']},
    'installable': True,
    'application': False,
}
