# -*- coding: utf-8 -*-
{
    'name': 'PG Website Scroll Back To Top',
    'summary': 'Botao "Voltar ao topo" em todas as paginas do website (modulo de terceiros).',
    'description': """
PG Website Scroll Back To Top (modulo de terceiros - Bytesfuel)
================================================================

a) Origem e estado no projeto Sofmovel
--------------------------------------
[FACTO OBSERVADO] modulo de terceiros (Bytesfuel, licenca LGPL-3). Mantido
no repositorio porque adiciona o botao "Back To Top" usado no website Sofmovel.

NAO alterar a logica interna do modulo - patches devem ser feitos por cima
em modulo proprio.

b) Objetivo de negocio (resumo do fornecedor)
---------------------------------------------
Adicionar um botao flutuante de "Voltar ao topo" em todas as paginas do
website (Shop, Blog, Eventos, etc.). O botao aparece apos scroll e leva o
utilizador ao topo da pagina ao clique.

c) Pre-requisitos
-----------------
- Modulo standard `website`.

d) Como funciona (resumo)
-------------------------
- `views/back_to_top.xml`: template QWeb que adiciona o markup do botao.
- `static/src/js/back_to_top.js`: JS frontend que mostra/esconde o botao
  conforme o scroll e gere o clique.
- `static/src/scss/back_to_top.scss`: estilos do botao.
- Registado em `web.assets_frontend`.

e) Passo a passo de utilizacao
------------------------------
1. Instalar o modulo.
2. O botao aparece automaticamente em todas as paginas do website apos
   scroll inicial.

f) FAQ / Resolucao de problemas
-------------------------------
- "Botao nao aparece":
  Limpar cache do browser (Ctrl+Shift+R). Validar que os assets sao
  servidos sem erro 404.
- "Quero mudar a aparencia":
  Editar `static/src/scss/back_to_top.scss`. Para evitar problemas em
  upgrades, fazer override no modulo proprio em vez de alterar diretamente.

g) Pontos de atencao (Sofmovel)
-------------------------------
- LGPL-3, livre de uso e modificacao. Ainda assim, recomenda-se nao
  alterar para facilitar adopcao de upgrades upstream.
- Modulo declara `application=True`; e irrelevante para o utilizador final.
    """,
    'category': 'Website',
    'version': '19.0.1.0.0',
    'author': "Bytesfuel",
    'website': "https://bytesfuel.com/",
    'license': 'LGPL-3',
    "sequence":  1,
    'data': [
        'views/back_to_top.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            '/pg_website_scroll_top_bytesfuel/static/src/js/back_to_top.js',
            '/pg_website_scroll_top_bytesfuel/static/src/scss/back_to_top.scss',
        ],
    },
    'images': ['static/description/banner.png'],
    'depends': ['website'],
    'installable': True,
    'application': True,
}
