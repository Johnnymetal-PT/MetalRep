# -*- coding: utf-8 -*-

{
    'name': 'PG Website Auth Required',
    'version': '19.0.1.0.0',
    'category': 'Website',
    'summary': 'Restringe loja/produtos a utilizadores autenticados com excecao de uma arvore publica.',
    'description': '''
Objetivo de negocio
===================
Protege a extranet comercial da Essani, permitindo navegação pública apenas numa árvore de categoria definida.

Pre-requisitos
==============
Website/eCommerce e `pg_web_attach_pdf_view` instalados. Parametro `pg_website_auth_required.public_root_category_id` deve apontar para a categoria pública permitida; valor inicial atual: 1817.

Como funciona
=============
Herda `WebsiteSale.shop` e `WebsiteSale.product`. Visitantes públicos só podem abrir categorias dentro da árvore configurada; produto e página `/categorias` exigem login. O modelo `website` calcula os IDs permitidos com domínio `child_of`.

Passo a passo de utilizacao
===========================
1. Configurar a categoria pública permitida no parametro de sistema. 2. Atualizar o modulo. 3. Testar como visitante anónimo: categoria permitida abre, produto redireciona para login. 4. Testar como portal/interno.

Exemplo pratico
===============
Se a categoria `Destaques` tiver ID 1817, visitantes conseguem abrir `/shop/category/destaques-1817`, mas ao clicar num produto são enviados para `/web/login?redirect=...`.

FAQ / Resolucao de problemas
============================
Se tudo redireciona para login, validar o ID do parametro. Se uma categoria não devia ser pública, removê-la da árvore configurada. Se a loja standard já está em `logged_in`, confirmar se a exceção pública ainda é necessária.

Pontos de atencao / avisos
==========================
Este modulo é a substituição local de `pg_website_shop_redirect`. O ID 1817 é específico da base atual e deve ser revisto após migrações/restauros.
''',
    'author': 'Parametro Global SA',
    'license': 'LGPL-3',
    'depends': ['website_sale', 'pg_web_attach_pdf_view'],
    'data': ['data/ir_config_parameter.xml'],
    'installable': True,
    'application': False,
}
