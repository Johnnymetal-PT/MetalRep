# -*- coding: utf-8 -*-

{
    'name': 'PG Limites de Email Marketing',
    'version': '19.0.1.0.0',
    'category': 'Marketing',
    'summary': 'Limita envios de email marketing por hora e por dia.',
    'description': '''
Objetivo de negocio
===================
Evita picos de envio que possam prejudicar reputação de domínio, limites SMTP ou entregabilidade das campanhas.

Pre-requisitos
==============
Modulo Email Marketing (`mass_mailing`) instalado. Cron/queue de email ativo. Utilizadores devem definir limites no mailing ou aceitar defaults 200/hora e 5000/dia.

Como funciona
=============
Herda `mail.mail._send`, separa emails com `mailing_id`, bloqueia a campanha com `SELECT ... FOR UPDATE NOWAIT`, consulta logs em `pg.email.marketing.log`, envia apenas a quota permitida e reagenda o excedente.

Passo a passo de utilizacao
===========================
1. Criar campanha de Email Marketing. 2. Definir limites horário/diário no envio agendado. 3. Agendar/enviar. 4. Monitorizar emails adiados e logs se houver throttling.

Exemplo pratico
===============
Campanha com 650 destinatários e limite 200/hora: os primeiros 200 seguem, os restantes são reagendados em blocos horários até terminar.

FAQ / Resolucao de problemas
============================
Se emails ficam em fila, verificar limites definidos, `scheduled_date` e logs `pg.email.marketing.log`. Se dois workers concorrem, o segundo adia a campanha por alguns minutos. Se o envio parece lento, confirmar se o limite não foi deixado demasiado baixo.

Pontos de atencao / avisos
==========================
Override de `_send` é sensível a alterações core do Mail. Usa commits/cron standard do Odoo; não contorna regras SMTP. Os limites são por campanha (`mailing.mailing`), não globais por servidor.
''',
    'license': 'LGPL-3',
    'depends': ['mass_mailing'],
    'data': ['security/ir.model.access.csv', 'views/mailing_mailing_views.xml'],
    'installable': True,
    'application': False,
}
