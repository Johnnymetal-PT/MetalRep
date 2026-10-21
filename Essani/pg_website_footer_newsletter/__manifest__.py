# -*- coding: utf-8 -*-
{
    'name': 'PG Website Rodapé e Newsletter traduzíveis',
    'version': '19.0.1.0.0',
    'category': 'Website',
    'summary': (
        'O rodapé e o bloco da newsletter do website Essani V5 passam a ser uma vista, '
        'traduzível em português, inglês e espanhol.'
    ),
    'description': '''
Objetivo de negocio
===================
O rodapé e a newsletter do website estavam só em português, em qualquer língua (tarefa 8244). Eram
criados pelos scripts ``pgV4Footer`` e ``pgNewsletter`` do código personalizado do website, com o
texto escrito no JavaScript, e o editor de traduções do Odoo só traduz o que está em vistas. Os links
também não levavam o prefixo da língua, por isso um visitante inglês ou espanhol voltava ao português
ao clicar.

O que faz
=========
Cria, só para o website escolhido, uma vista que acrescenta antes do rodapé standard o mesmo HTML
que o JavaScript criava (bloco da newsletter e rodapé), mas escrito em inglês na base, com o
português e o espanhol aplicados como traduções. Os links passam a levar o prefixo da língua
automaticamente. Os scripts antigos terminam logo se os elementos já existirem, por isso ficam
inertes sem serem apagados.

Pre-requisitos
==============
- Aplicação ``website`` instalada, com as línguas pt_PT e es_ES.
- Um website com o nome ``Essani V5``. Se o nome for outro, definir o parâmetro de sistema
  ``pg_website_footer_newsletter.website_name`` **antes** de instalar. Se o website não existir, o
  módulo instala-se mas não cria nada.
- O CSS de ``.pg-nl`` e ``.pg-foot`` já existe no código personalizado do website.

Passo a passo de utilizacao
===========================
1. Instalar o módulo.
2. Abrir o site V5 em português, inglês e espanhol e ver o rodapé e a newsletter.
3. Para mudar um texto ou uma tradução: editar a vista "PG Rodapé e Newsletter" ou usar o editor
   de traduções do website.
4. Para voltar atrás: desinstalar o módulo (apaga a vista; os scripts antigos voltam a criar o
   rodapé em português).

FAQ / Resolucao de problemas
============================
*Vejo o rodapé duplicado.* Algum script do código personalizado criou o rodapé antes da vista.
Os scripts ``pgV4Footer`` e ``pgNewsletter`` verificam ``.pg-foot`` e ``.pg-nl`` e não fazem nada
se já existirem; se aparecer duplicado, é de outro código que cria um rodapé próprio.

Pontos de atencao / avisos
==========================
- O formulário da newsletter é um ``iframe`` da Brevo (sibforms). O módulo traduz o título e o
  texto à volta, mas **o texto do próprio formulário** (campos e botão) é o do formulário na Brevo,
  que está numa só língua. Para ter o formulário em inglês e em espanhol é preciso criar um
  formulário por língua na Brevo e indicar aqui os endereços.
- O rodapé aparece em todas as páginas, incluindo as de checkout e as de portal, como acontecia com
  o JavaScript.
- A morada, o telefone e o email são iguais em todas as línguas e não têm tradução.
''',
    'author': 'Parametro Global',
    'website': 'https://parametro.global',
    'license': 'LGPL-3',
    'depends': ['website'],
    'data': [],
    # A vista nasce no hook, ligada so ao website escolhido: se viesse num ficheiro de dados valia
    # para TODOS os websites da base (incluindo o site publico).
    'post_init_hook': 'post_init_criar_vista',
    'installable': True,
    'application': False,
    'auto_install': False,
}
