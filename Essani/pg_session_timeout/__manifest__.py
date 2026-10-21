# -*- coding: utf-8 -*-

{
    'name': 'PG Tempo de Sessao',
    'version': '19.0.1.0.0',
    'category': 'Tools',
    'summary': 'Alinha cookie de sessao com o tempo maximo de inatividade.',
    'description': '''
Objetivo de negocio
===================
Evita sessões web com cookies mais longos que o tempo de inatividade pretendido pela operação.

Pre-requisitos
==============
Parametro `sessions.max_inactivity_seconds` definido; valor default do modulo: 43200 segundos (12 horas). Requer reinício para aplicar `post_load`.

Como funciona
=============
No `post_load`, faz patch a `HttpRequest._save_session` e ao controller de autenticação para definir `max_age` no cookie `session_id`. Também herda `ir.http._gc_sessions` para usar o mesmo valor no vacuum.

Passo a passo de utilizacao
===========================
1. Definir o parametro de sistema se necessário. 2. Atualizar modulo e reiniciar Odoo.sh. 3. Fazer login e validar expiração do cookie no browser.

Exemplo pratico
===============
Com 43200 segundos, o cookie `session_id` fica com max-age de 12 horas e sessões antigas são limpas com o mesmo limite.

FAQ / Resolucao de problemas
============================
Se não aplica, reiniciar worker. Se utilizadores caem cedo demais, aumentar o parametro. Se o parametro tem texto inválido, o modulo usa o default Odoo e regista warning.

Pontos de atencao / avisos
==========================
Monkey patch em `post_load`: sensível a alterações internas do Odoo Web. Manter testes básicos de login após upgrades.
''',
    'license': 'LGPL-3',
    'depends': ['base', 'web'],
    'data': ['data/ir_config_parameter.xml'],
    'post_load': 'post_load',
    'installable': True,
    'application': False,
}
