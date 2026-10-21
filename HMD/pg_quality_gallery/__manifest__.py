# -*- coding: utf-8 -*-
{
    'name': 'PG Quality Gallery',
    'version': '18.0.1.0.0',
    'summary': 'Vista galeria (kanban) das verificacoes de qualidade com foto.',
    'description': """
PG Quality Gallery
==================

a) Objetivo de negocio
----------------------
Na HMD, muitas verificacoes de qualidade usam o tipo de teste "Tirar
uma Foto" para registar o estado do mobiliario. O standard mostra a
foto dentro de cada verificacao, mas nao oferece uma visao em galeria
para rever rapidamente varias fotos. Este modulo adiciona uma vista
kanban tipo galeria sobre `quality.check`, mais um menu dedicado.

b) Pre-requisitos
-----------------
- Odoo 18.0 Enterprise (versao ativa em PG_CONTEXT.md).
- Modulo `quality_control` (fornece `quality.check` e o campo binario
  `picture`).

c) Como funciona (tecnico)
--------------------------
1. Vista kanban `quality.check.kanban.gallery` (`views/...`): cartoes
   com a `picture` (widget image) + nome, produto, fornecedor, rececao
   e estado (badge verde/vermelho conforme aprovado/reprovado).
   Usa a sintaxe de kanban do Odoo 18 (`<t t-name="card">`).
2. Acao `quality_check_action_gallery`: abre a galeria com dominio
   `picture != False` (so verificacoes com foto). view_mode
   kanban,list,form para permitir alternar.
3. Menu "Galeria de Qualidade" sob Qualidade > Controlo de Qualidade.

d) Passo a passo de utilizacao
------------------------------
1. Instalar `pg_quality_gallery`.
2. Qualidade > Controlo de Qualidade > Galeria de Qualidade.
3. Ver as fotos das verificacoes em galeria; clicar abre a verificacao.

e) Pontos de atencao / avisos
-----------------------------
- So aparecem verificacoes que JA tem foto (`picture` preenchida).
- Sem desenvolvimento sobre `vendor/odoo_src`; apenas vista + acao +
  menu no namespace `pg_`. Vista carece de confirmacao visual no
  ambiente (kanban nao e validavel headless).
""",
    'author': 'Parametro Global',
    'website': 'https://parametro.global',
    'license': 'LGPL-3',
    'depends': ['quality_control'],
    'data': [
        'views/quality_gallery_views.xml',
    ],
    'installable': True,
    'application': False,
}
