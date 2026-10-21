# -*- coding: utf-8 -*-

{
    'name': 'PG PHC Contactos',
    'version': '2.1.4',
    'category': 'Contacts',
    'summary': 'Sincroniza clientes e moradas entre Odoo e PHC CSWeb.',
    'description': '''
Objetivo de negocio
===================
Mantém Odoo e PHC alinhados para clientes, campos comerciais e moradas de entrega durante a coexistência dos sistemas.

Pre-requisitos
==============
Credenciais CSWeb configuradas em Definições da empresa. Campos PHC/Studio criados por hooks ou existentes. Utilizadores internos configurados com número vendedor PHC e nome de responsável interno. Condições de pagamento, país, NIF e dados obrigatórios preenchidos.

Como funciona
=============
Herda `res.partner` e `res.users`. Cria/atualiza clientes por SOAP `RunCode` (`CriaCL`, `UpdateCL`) e moradas por `Cria_MoradaEntregaCL`. Valida campos obrigatórios e limites PHC, bloqueia alterações de NIF quando há documentos, trata duplicados e faz auto-sync controlado no create/write.

Regra do NIF no payload PHC: o `CriaCL` envia sempre `ncont`/`pncont`; o `UpdateCL` só os envia quando a gravação alterou mesmo o NIF no Odoo. O PHC recusa qualquer `UpdateCL` que traga o NIF de um cliente com documentos certificados emitidos, mesmo que o NIF seja igual ao que já tem — enviá-lo sempre fazia com que uma alteração de outro campo (ex: termos de pagamento) fosse recusada pelo PHC e perdida no Odoo.

Passo a passo de utilizacao
===========================
1. Configurar URL/utilizador/password PHC. 2. Configurar vendedores/responsáveis nos utilizadores. 3. Preencher ficha de cliente. 4. Clicar `PHC Sync` para criar ou `PHC Update` para atualizar. 5. Consultar `Última resposta PHC`.

Exemplo pratico
===============
Cliente empresa PT com NIF, morada, vendedor e pagamento preenchidos é enviado por `CriaCL`; o PHC devolve número, que é guardado como referência efetiva no contacto.

FAQ / Resolucao de problemas
============================
Sync bloqueado: ler lista de campos em falta no popup. PHC não devolveu referência: consultar resposta bruta. NIF duplicado: resolver duplicado salvo exceções `999999990`/`SEM NIF`. Morada de entrega falha: garantir cliente principal já sincronizado.

"Não pode alterar o NIF numa ficha de cliente já existente e com documentos certificados já emitidos": mensagem devolvida pelo PHC, não do Odoo. Se aparecer numa gravação em que o NIF foi alterado, é bloqueante e correta. Se surgir num `UpdateCL` sem NIF no payload, a gravação no Odoo passa e fica registada uma nota no contacto mais o marcador `[PG_PHC_VAT_LOCK]` em `Última resposta PHC` — nesse caso o PHC não recebeu a atualização e é preciso validar com o PHC a referência (`no`) e o `ncont` da ficha; ver a linha `PHC parameter XML built for partner` nos logs para o payload exato.

Pontos de atencao / avisos
==========================
Integração crítica e específica do contrato CSWeb. Não alterar códigos de scripts PHC, limites ou mapeamentos sem validação com PHC. Hooks criam colunas/campos para evitar falhas de registry em upgrades.
''',
    'author': 'Parametro Global',
    'license': 'LGPL-3',
    'depends': ['base', 'account'],
    'data': ['views/res_partner_views.xml',
 'views/res_config_settings_views.xml',
 'views/res_users_views.xml'],
    'pre_init_hook': 'pre_init_hook',
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
}
