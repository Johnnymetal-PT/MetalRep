# -*- coding: utf-8 -*-

{
    'name': 'PG Filtro de Categorias Visiveis',
    'version': '1.1',
    'category': 'Website',
    'summary': 'Oculta categorias sem produtos visiveis no menu da loja.',
    'description': '''
Objetivo de negocio
===================
Evita que clientes vejam categorias vazias depois da regra de visibilidade por cliente/visitante filtrar produtos.

Pre-requisitos
==============
`website_product_visibility` ativo e configurado. Website/eCommerce instalado.

Como funciona
=============
Depois do `WebsiteSale.shop`, calcula produtos visíveis com `website.sale_product_domain()`, recolhe categorias públicas desses produtos e respetivos pais, e passa IDs ao qcontext. O template `categories_recursive` só renderiza categorias permitidas.

Passo a passo de utilizacao
===========================
1. Configurar visibilidade por cliente/visitante. 2. Abrir loja com esse utilizador. 3. Confirmar que o menu mostra apenas categorias com produtos acessíveis.

Exemplo pratico
===============
Cliente A só pode ver produtos de `Cadeiras`. O menu deixa de mostrar `Mesas` se não houver produtos visíveis nessa categoria.

FAQ / Resolucao de problemas
============================
Se uma categoria esperada desaparece, confirmar que pelo menos um produto publicado pertence a essa categoria pública. Se pais desaparecem, validar árvore de categorias públicas.

Pontos de atencao / avisos
==========================
Calcula visibilidade por pedido e usa `sudo()` para ler produtos, mas aplica o domínio final de website. Depende dos efeitos de `website_product_visibility.sale_product_domain()`.
''',
    'author': 'Joao Barros / Parametro Global',
    'depends': ['website_sale', 'website_product_visibility'],
    'data': ['views/website_sale_category_menu.xml'],
    'installable': True,
    'application': False,
}
