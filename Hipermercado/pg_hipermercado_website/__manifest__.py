# -*- coding: utf-8 -*-
#
# Manifesto do modulo PG Hipermercado Website.
#
# Ajustes de frontend especificos do Hipermercado.pt. Nesta primeira versao
# corrige a performance do mega menu "Produtos": ao abrir, o menu (dropdown
# full-width) forcava o recalculo de layout/paint e dos IntersectionObservers
# de toda a pagina (~548 imagens em ~23 snippets dinamicos), bloqueando a
# thread principal varios segundos (freeze intermitente, pior em maquinas
# medias). A correcao aplica content-visibility aos snippets dinamicos para
# que os que estao fora do ecra nao sejam renderizados ate entrarem na
# viewport.
#
# Idioma da documentacao: Portugues (Portugal).

{
    "name": "PG Hipermercado Website",
    "summary": "Ajustes de website do Hipermercado.pt (performance do mega menu via content-visibility).",
    "description": """
PG Hipermercado Website
=======================

Ajustes de frontend especificos do Hipermercado.pt.

1. Performance do mega menu
---------------------------
A homepage carrega cerca de 548 imagens distribuidas por ~23 snippets
dinamicos. O mega menu "Produtos" e um dropdown full-width; ao abrir, o
browser recalculava o layout, os IntersectionObservers e o paint da pagina
inteira, bloqueando a thread principal por varios segundos (medido: ~9-18 s
com CPU 6x).

A correcao aplica ``content-visibility: auto`` aos snippets dinamicos, pelo
que os que estao fora do ecra deixam de ser renderizados ate entrarem na
viewport. Abrir o mega menu deixa de forcar um recalculo de pagina inteira
(medido: bloqueio < 100 ms depois da correcao).
""",
    "version": "19.0.1.0.0",
    "category": "Website",
    "author": "Parametro Global",
    "license": "LGPL-3",
    "depends": ["website"],
    "assets": {
        "web.assets_frontend": [
            "pg_hipermercado_website/static/src/scss/mega_menu_perf.scss",
        ],
    },
    "installable": True,
    "application": False,
}
