# -*- coding: utf-8 -*-

{
    'name': 'PG Website Botao Voltar ao Topo',
    'version': '1.0',
    'category': 'Website',
    'summary': 'Adiciona botao de voltar ao topo nas paginas do website.',
    'description': '''
Objetivo de negocio
===================
Melhora a navegação em páginas longas, permitindo regressar ao topo sem scroll manual extenso.

Pre-requisitos
==============
Modulo Website instalado e assets frontend carregados.

Como funciona
=============
Injeta template do botão no website e adiciona JS/SCSS frontend para mostrar/esconder e animar o scroll.

Passo a passo de utilizacao
===========================
1. Instalar o modulo. 2. Abrir uma página longa. 3. Fazer scroll para baixo. 4. Clicar no botão para regressar ao topo.

Exemplo pratico
===============
Na loja com grelha de muitos produtos, após descer várias linhas, o botão aparece e leva o utilizador ao cabeçalho.

FAQ / Resolucao de problemas
============================
Se o botão não aparece, limpar assets e confirmar que `web.assets_frontend` inclui o JS/SCSS. Se sobrepõe outro elemento, ajustar SCSS.

Pontos de atencao / avisos
==========================
Modulo visual simples. Sem dados próprios. Veio de addon externo Bytesfuel; manter alterações pequenas para facilitar upgrades.
''',
    'author': 'Bytesfuel, adaptado PG',
    'website': 'https://bytesfuel.com/',
    'license': 'LGPL-3',
    'sequence': 1,
    'depends': ['website'],
    'data': ['views/back_to_top.xml'],
    'assets': {'web.assets_frontend': ['/pg_website_scroll_top_bytesfuel/static/src/js/back_to_top.js',
                         '/pg_website_scroll_top_bytesfuel/static/src/scss/back_to_top.scss']},
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
}
