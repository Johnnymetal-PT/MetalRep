# -*- coding: utf-8 -*-
{
    'name': 'PG Website Hero: a luz acende',
    'version': '19.0.1.3.0',
    'category': 'Website',
    'summary': (
        'Animação de entrada no Hero da homepage: o Hero está às escuras e a luz acende. '
        'Só para o website Essani V5.'
    ),
    'description': '''
Objetivo de negocio
===================
A cliente pediu, para o novo site, a animação do Hero ao estilo do site da Halemeier. Esclareceu
por email a 14/10 que se referia só ao que o Hero dessa página faz, e não à página de cenas com
scroll (``pg_website_scroll_scenes``): uma coisa só, no Hero da entrada, com a luz a acender.
Pedido na reunião de 16/10 (tarefa 8241).

O que faz
=========
Ao carregar a homepage, o Hero começa às escuras. O brilho dourado nasce e cresce, o fundo
"acende" com uma hesitação, e só depois sobe o texto, linha a linha. Dura 6,5 s e acaba no Hero
tal como já era. Os tempos estão em variáveis ``--pg-luz-*`` no topo do CSS. É só CSS (``static/src/css/pg_hero_luz.css``): não edita a vista da homepage
nem o código personalizado do website.

Pre-requisitos
==============
- Aplicação ``website`` instalada.
- Um website com o nome ``Essani V5``. Se o nome for outro, definir o parâmetro de sistema
  ``pg_website_hero_luz.website_name`` **antes** de instalar. Se o website não existir, o módulo
  instala-se mas não liga nada.
- A homepage tem de manter a estrutura ``#wrap.pgh > section.hero`` com um ``.glow`` e um
  ``.wrp``, que é a do Hero atual.

Passo a passo de utilizacao
===========================
1. Instalar o módulo.
2. Abrir a homepage do V5 com o separador novo (ou ``Ctrl+F5``) para ver a animação desde o
   início. Corre uma vez por carregamento da página (cerca de 6,5 s).
3. Para voltar atrás: desinstalar o módulo.

FAQ / Resolucao de problemas
============================
*Instalei e não se nota nada.* O site visto não é o V5, ou o sistema tem a preferência
*reduzir movimento* ligada (com ela o Hero aparece sem animação, de propósito).

*Quero outro ritmo.* Mexer nas variáveis ``--pg-luz-*`` no topo do CSS; a linha do tempo
está explicada no comentário inicial.

Pontos de atencao / avisos
==========================
- O Hero já tem animações próprias (brilho que respira, brilho que passa, canvas). O módulo
  só acrescenta uma entrada por cima; entrega o brilho à respiração original aos 6 s.
- Os botões lado a lado do Hero ("Ver catálogo" e "Seja parceiro") e da secção final ("Ver
  catálogo" e "Falar connosco") ficam com a mesma largura, a do mais largo; em ecrãs estreitos
  empilham-se.
- O menu hambúrguer no telemóvel fechava ao tocar numa opção, sem abrir a página: um
  `.offcanvas-backdrop{z-index:1290!important}` do código personalizado (feito para o carrinho)
  cobria o menu, que vive dentro do cabeçalho (z-index 1050). O módulo repõe o backdrop a 1040
  só enquanto o menu está aberto; o do carrinho não muda.
- Não cobre as páginas de campanha nem as internas: só o Hero com ``#wrap.pgh``.
''',
    'author': 'Parametro Global',
    'website': 'https://parametro.global',
    'license': 'LGPL-3',
    'depends': ['website'],
    'data': [],
    # O asset nao vai em `assets` do manifesto: isso aplicava-o a TODOS os websites.
    # O hook cria-o ligado so ao website escolhido.
    'post_init_hook': 'post_init_ligar_ao_website',
    'installable': True,
    'application': False,
    'auto_install': False,
}
