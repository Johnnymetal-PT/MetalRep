# -*- coding: utf-8 -*-

{
    'name': 'PG PHC Faturas',
    'version': '19.0.1.0.1',
    'category': 'Accounting',
    'summary': 'Sincroniza faturas de venda Odoo para PHC CSWeb.',
    'description': '''
Objetivo de negocio
===================
Garante que faturas emitidas no Odoo são criadas no PHC durante o período de coexistência com o ERP legado.

Pre-requisitos
==============
Conector `pg_phc_api` configurado na empresa com URL, utilizador e password PHC. Cliente da fatura sincronizado e com número PHC. Campos fiscais PHC configurados: doctype, tabela IVA, tipo de artigo. Acesso de rede ao CSWeb.

Como funciona
=============
Herda `account.move` e sincroniza no `_post` ou por botão manual. Monta XML SOAP `RunCode` com `CriaFT` ou `CriaFTAD`, trata adiantamentos, notas, quebras de descrição, referências de adiantamento e anexa o PDF devolvido pelo PHC.

Passo a passo de utilizacao
===========================
1. Configurar credenciais PHC na empresa. 2. Sincronizar cliente pelo `pg_phc_api`. 3. Validar impostos/produtos. 4. Confirmar/postar fatura. 5. Verificar `ERP Synced`, `PHC Last Response` e PDF anexado.

Exemplo pratico
===============
Fatura normal de 2 linhas chama `CriaFT`; uma fatura de adiantamento chama `CriaFTAD`, guarda Ano/FT_Adiantamento e a fatura final envia esses dados em `adano/adnum`.

FAQ / Resolucao de problemas
============================
Erro `Partner has no PHC number`: sincronizar cliente primeiro. Sem PDF: consultar `PHC Last Response`. Duplicação: confirmar se `is_phc_synced` não foi desmarcado indevidamente. Erros SSL/rede: validar URL CSWeb e conectividade Odoo.sh.

Pontos de atencao / avisos
==========================
Usa `verify_ssl=False` por compatibilidade com endpoint PHC; rever quando houver certificado válido. Envio automático no `_post` tem impacto operacional: testar faturas de adiantamento e finais antes de alterar.
''',
    'author': 'Odoo PS / Parametro Global',
    'website': 'https://www.odoo.com',
    'license': 'LGPL-3',
    'depends': ['sale_stock', 'sale_management', 'pg_phc_api'],
    'data': ['views/account_move_views.xml'],
    'installable': True,
    'application': False,
}
