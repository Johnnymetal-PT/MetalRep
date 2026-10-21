# -*- coding: utf-8 -*-
{
    'name': 'PG Website Casos Reais: cartões editáveis',
    'version': '19.0.1.0.0',
    'category': 'Website',
    'summary': (
        'Permite acrescentar, retirar, mover e mudar de setor os cartões dos casos reais da '
        'página Inspiração, no editor do website.'
    ),
    'description': '''
Objetivo de negocio
===================
A Essani tem de poder acrescentar e retirar cartões na secção dos casos reais da página
Inspiração, sem nos pedir (tarefa 8242, pedido da reunião de 16/10). Está relacionada com a
tarefa 8243: é o mesmo problema de fundo, o conteúdo desenhado fora do que o editor do Odoo
sabe gerir.

O que faz
=========
Os cartões são ``div.case`` simples numa grelha ``.pg-cases``, filtrados por um script
(``data-sector``). O construtor do Odoo 19 só oferece clonar, remover e mover em blocos que
tenham uma opção registada, e nenhuma das do standard apanha este ``div``. O módulo regista duas
opções no construtor:

- no **cartão** (``.pg-cases .case``): o seletor de **Setor**, que escreve ``data-sector``, e a
  possibilidade de o mover; clonar e remover vêm dos botões do próprio construtor;
- na **grelha** (``.pg-cases``): o botão **Adicionar cartão**, que duplica o último.

Não edita nenhuma vista nem o código personalizado do website, e não altera o desenho: é só o
que o editor passa a oferecer.

Pre-requisitos
==============
- Aplicação ``website`` instalada (Odoo 19, construtor novo ``html_builder``).
- Os cartões têm de manter a estrutura ``.pg-cases > .case[data-sector]`` da página Inspiração.

Passo a passo de utilizacao
===========================
1. Instalar o módulo e recarregar o editor do website.
2. Abrir a página Inspiração do website V5 em edição e clicar num cartão.
3. Acrescentar: botão de duplicar do cartão, ou **Adicionar cartão** nas opções da grelha. O
   cartão novo herda a imagem e o setor do cartão copiado.
4. Trocar a imagem: clicar nela e escolher **Substituir**. Mudar a etiqueta: escrever no texto.
5. Mudar o setor: opção **Setor** do cartão (para o filtro da página o apanhar).
6. Retirar: botão de remover do cartão.

FAQ / Resolucao de problemas
============================
*Não aparecem as opções.* O editor tem de ser recarregado depois de instalar o módulo
(``Ctrl+F5``), e a página tem de ter a grelha ``.pg-cases``.

*Acrescentei um setor novo ao filtro da página.* Acrescentá-lo também em
``static/src/builder/cases_option.xml``, com o mesmo valor que o ``data-f`` do botão.

Pontos de atencao / avisos
==========================
- Os assets do construtor aplicam-se a todos os websites da base; os seletores só apanham
  ``.pg-cases``, por isso nos outros nada muda.
- Um cartão clonado fica com o ``alt`` da imagem do original. Se a imagem for trocada, convém
  atualizar o texto alternativo.
- A etiqueta (``.tag``) e o ``alt`` não são traduzidos automaticamente com o setor.
''',
    'author': 'Parametro Global',
    'website': 'https://parametro.global',
    'license': 'LGPL-3',
    'depends': ['website'],
    'data': [],
    'assets': {
        'website.website_builder_assets': [
            'pg_website_cases_editor/static/src/builder/**/*',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
