# -*- coding: utf-8 -*-

{
    'name': 'PG Bypass Validacao VAT em Importacao',
    'version': '1.0.6',
    'category': 'Contacts',
    'summary': 'Permite importar contactos legados sem bloquear por VAT invalido.',
    'description': '''
Objetivo de negocio
===================
Permite carregar dados legados de clientes mesmo quando NIF/VAT antigo não passa a validação standard, sem desligar validação em gravações manuais normais.

Pre-requisitos
==============
Modulo `base_vat` instalado. Usar importador standard Odoo ou ativar temporariamente parametro `pg_import_bypass.disable_vat_check` quando o contexto de importação não propaga.

Como funciona
=============
Herda `res.partner` e intercepta `_run_vat_checks`, `_check_vat_number`, `check_vat`, `_run_vat_test` e `simple_vat_check`. O bypass ativa com contexto `import_file`, contexto `no_vat_validation` ou parametro de sistema truthy.

Passo a passo de utilizacao
===========================
1. Para import normal, usar o importador Odoo. 2. Se o botão Teste ainda bloquear, ativar parametro `pg_import_bypass.disable_vat_check = 1`. 3. Importar. 4. Desativar o parametro imediatamente após a importação.

Exemplo pratico
===============
Importação de cliente com VAT `A` deixa de falhar na validação de tamanho/checksum durante o upload legado.

FAQ / Resolucao de problemas
============================
Se ainda falha, confirmar se o erro vem de outro constraint (por exemplo duplicado PHC). Se bypass afeta gravações manuais, verificar se o parametro ficou ligado. Se há logs warning, são esperados para auditoria.

Pontos de atencao / avisos
==========================
Usar apenas em janelas controladas de importação. O parametro global é perigoso se ficar ativo, porque ignora validação VAT em todas as gravações.
''',
    'author': 'Parametro Global',
    'license': 'LGPL-3',
    'depends': ['base', 'base_vat'],
    'data': [],
    'installable': True,
    'application': False,
}
