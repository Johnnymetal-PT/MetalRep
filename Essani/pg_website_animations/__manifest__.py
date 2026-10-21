# -*- coding: utf-8 -*-
{
    'name': 'PG Website Animações',
    'version': '19.0.1.0.0',
    'category': 'Website',
    'summary': (
        'Animações discretas para o website Essani V4: botões que se preenchem, '
        'imagens que reagem ao rato e blocos que entram ao fazer scroll.'
    ),
    'description': '''
Objetivo de negocio
===================
A cliente pediu um site "mais moderno", com mais movimento ao longo das páginas, tendo
como referência o site da Halemeier. O que se pede, na prática, é feedback visual ao
passar o rato e uma entrada suave dos blocos — sem desfazer a linha sóbria em que o V4
já assentou.

Este módulo acrescenta só isso, e **só ao website escolhido** (por omissão ``Essani V4``).
Não edita nenhuma vista nem nenhum snippet: é uma folha de estilos e um script pequeno.
Desinstalar o módulo devolve o site exatamente ao que era.

Pre-requisitos
==============
- Aplicação ``website`` instalada.
- Um website com o nome ``Essani V4``. Se o nome for outro, definir o parâmetro de sistema
  ``pg_website_animations.website_name`` **antes** de instalar. Se o website não existir, o
  módulo instala-se mas não liga nada — nunca se aplica a todos os websites por engano.

Como funciona
=============
**Botões.** Os botões primários e secundários ganham uma varredura de cor da esquerda para a
direita ao passar o rato; os botões de contorno enchem-se com a cor da marca.

**Imagens.** Os cartões sobem ligeiramente e a imagem amplia-se de leve. O mesmo nas imagens
de categorias e de produtos nas listas da loja.

**Entrada ao fazer scroll.** Cartões, categorias, colunas de características e produtos
aparecem com um deslize curto e um fade, em cascata. Só se aplica a elementos que ainda não
estão visíveis ao abrir a página, e não toca nos que já têm animação própria do Odoo
(``o_animate``).

Respeita a preferência de sistema *reduzir movimento*: com ela ligada, nada se anima. Também
não corre no editor do website.

Passo a passo de utilizacao
===========================
1. Instalar o módulo.
2. Abrir o website V4 (``/?fw=<id do website>``) e percorrer a página inicial e as famílias.
3. Para voltar atrás: desinstalar o módulo (Aplicações > PG Website Animações > Desinstalar).

FAQ / Resolucao de problemas
============================
*Instalei e não se nota nada.* O site visto não é o V4. Confirmar o nome do website no
parâmetro ``pg_website_animations.website_name``, e voltar a instalar. Se o website não
existia na altura da instalação, os assets não foram criados.

*Quero as animações noutro website.* Definir o parâmetro, desinstalar e voltar a instalar.

*Um elemento específico não deve animar.* Acrescentar-lhe a classe ``pg-no-anim``.

Pontos de atencao / avisos
==========================
- Os seletores da entrada ao scroll estão na lista ``ALVOS`` de ``static/src/js/pg_reveal.js``.
  Um snippet novo só anima se for acrescentado lá.
- Isto é uma interpretação de "mais moderno". Se a cliente quiser mais ou menos movimento,
  ajustam-se as durações e distâncias nas variáveis ``--pg-*`` no início do CSS.
''',
    'author': 'Parametro Global',
    'website': 'https://parametro.global',
    'license': 'LGPL-3',
    'depends': ['website'],
    'data': [],
    # Os assets nao vao em `assets` do manifesto: isso aplicava-os a TODOS os websites.
    # O hook cria-os ligados so ao website escolhido.
    'post_init_hook': 'post_init_criar_assets',
    'installable': True,
    'application': False,
    'auto_install': False,
}
