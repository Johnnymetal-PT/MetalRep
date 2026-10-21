# -*- coding: utf-8 -*-
{
    'name': 'PG Product Description',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': 'Injeta um texto fixo informativo (regras de metragens, padroes, rugas, tolerancia 2-4%) abaixo da descricao do produto no website (template product_template_custom_text).',
    'author': 'Parametro Global',
    'depends': ['sale', 'website_sale'],
    'data': [
        'views/product_template_inherit.xml',
    ],
    'description': """
PG Product Description
======================

a) Objetivo de negocio
----------------------
Mostrar em todas as fichas publicas de produto da Piccolo uma nota
legal/comercial sobre:
- Metragens apresentadas referem-se a 1 tecido.
- Variacao por padrao.
- Variacao de rugas/engelhas conforme tipo.
- Tolerancia dimensional de 2% a 4%.

Evita ter de repetir este texto em cada produto manualmente e
garante coerencia juridica.

b) Pre-requisitos
-----------------
- Modulos standard ``sale`` e ``website_sale``.

c) Como funciona
----------------
- ``views/product_template_inherit.xml`` faz inherit de
  ``website_sale.product`` e injeta um ``<div class="custom-product-info">``
  com o texto literal a seguir ao paragrafo ``text-muted my-2``
  (descricao standard do produto).
- Nao tem Python, nao tem assets.

d) Passo a passo de utilizacao
------------------------------
1. Instalar.
2. Abrir qualquer ficha publica de produto - o texto aparece
   abaixo da descricao.

e) Exemplo pratico
------------------
Ficha de "Cadeira X" mostra a descricao do produto e, logo abaixo:
::

    As metragens apresentadas são apenas para 1 único tecido.
    As metragens mencionadas podem variar mediante o padrão do tecido.
    Os artigos podem ter variações mais acentuadas de rugas / engelhas
    mediante o tipo de tecido.
    As medidas apresentadas podem ter variações de 2% a 4%.

f) FAQ / Resolucao de problemas
-------------------------------
- *"Texto nao aparece"* -> outra customizacao alterou a classe
  ``text-muted my-2`` no template; reavaliar o xpath.
- *"Quero esconder em alguns produtos"* -> nao suporta condicional
  no template. Para mostrar so em algumas categorias, adicionar
  ``t-if`` ao bloco no XML.

g) Pontos de atencao / avisos
-----------------------------
- Texto HARDCODED no XML - mudar copy implica deploy.
- O xpath assume que existe ``<p class='text-muted my-2'>`` no
  template standard. Em upgrades Odoo onde o markup mude, o
  xpath falha em silencio.
""",
    'installable': True,
}
