# -*- coding: utf-8 -*-
{
    'name': 'PG Website Cenas com Scroll',
    'version': '19.0.1.3.0',
    'category': 'Website',
    'summary': (
        'Secções fixas cuja animação avança com o scroll, ao estilo do site da Halemeier. '
        'Só para o website Essani V5.'
    ),
    'description': '''
Objetivo de negocio
===================
A cliente quer, para o novo site, animações que só avançam com o scroll: a secção fica
fixa no ecrã e, à medida que se desce, os textos e as imagens vão entrando e saindo; se se
voltar atrás, a animação recua. A referência é https://smart-home-by-halemeier.de/.

Este módulo traz o motor dessas "cenas" e uma página (``/cenas-scroll``) com todo o conteúdo da
homepage do V5 reorganizado em onze cenas, com as imagens, textos e links da própria Essani. Não edita nenhuma vista nem nenhum snippet
existente, e **só se liga ao website escolhido** (por omissão ``Essani V5``).

Pre-requisitos
==============
- Aplicação ``website`` instalada.
- Um website com o nome ``Essani V5``. Se o nome for outro, definir o parâmetro de sistema
  ``pg_website_scroll_scenes.website_name`` **antes** de instalar. Se o website não existir,
  o módulo instala-se mas não liga nada.

Como funciona
=============
Usa GSAP + ScrollTrigger (incluídos no módulo, versão 3.12.5, licença standard da GreenSock).
Uma secção com ``data-pg-scene`` fica fixa durante ``n`` ecrãs de scroll, onde ``n`` é o maior
``data-pg-step``. Cada elemento com ``data-pg-step="k"`` entra no passo ``k`` e sai antes do
seguinte (o último fica).

Atributos úteis (ver a página ``/cenas-scroll`` do website para exemplos):

- ``data-pg-step="k"``: em que passo aparece o elemento.
- ``data-pg-from="up|down|left|right|zoom|fade"``: de onde entra.
- ``data-pg-align="center|bottom"``: onde fica o texto.
- ``data-pg-keep``: o elemento não sai no fim do seu passo.
- Na secção: ``data-pg-zoom="1.2"`` (aproximação do fundo) e ``data-pg-veil="0.3,0.7"``
  (opacidade inicial e final do véu).
- ``.pg-scene__layer`` com ``data-pg-step``: imagens que se trocam por fusão; ``data-pg-dur``
  controla a duração da fusão, em fração de um passo (0.9 faz a luz "acender" devagar).
- Na secção: ``data-pg-vh="0.7"`` muda o scroll gasto por passo (por omissão 0.9 ecrãs).

Só liga em ecrã largo (>= 992 px), sem a preferência de sistema *reduzir movimento* e fora do
editor do website. Em qualquer outro caso (telemóvel, sem JavaScript, editor) a cena aparece
como uma coluna normal com todos os passos visíveis.

Passo a passo de utilizacao
===========================
1. Instalar o módulo.
2. Abrir ``/cenas-scroll?fw=<id do website V5>`` e fazer scroll.
3. Atualizar o módulo repõe o conteúdo da página ``/cenas-scroll`` com o do ficheiro
   ``data/demo_page_arch.xml`` (edições feitas à mão nessa página perdem-se).
4. Para voltar atrás: desinstalar o módulo (apaga também a página).

FAQ / Resolucao de problemas
============================
*Instalei e não se nota nada.* O site visto não é o V5. Confirmar o nome do website no
parâmetro e voltar a instalar.

*A cena não fica fixa.* Se algum ancestral tiver ``overflow``/``transform`` pode quebrar o
efeito. O motor deteta o ``#wrapwrap`` como contentor de scroll, mas um bloco novo à volta da
cena pode estragá-lo.

*Quero outro ritmo.* ``VH_POR_PASSO`` em ``static/src/js/pg_scenes.js`` controla o scroll
gasto por passo (0.9 ecrãs).

Pontos de atencao / avisos
==========================
- O V5 herdou do V4 um script de entrada por scroll no código personalizado do website, que
  usa as classes ``pg-reveal``/``pg-in``. A folha de estilos deste módulo neutraliza-as dentro
  das cenas, mas fora delas os dois efeitos coexistem.
- A página de demonstração tem os textos em português no idioma base; não tem traduções.
- Cada cena é desenhada à mão (imagens, textos, número de passos). Não é um efeito que se
  aplique por classe a qualquer secção.
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
