# -*- coding: utf-8 -*-
{
    "name": "PHC Connector",
    "version": "2.0.3",
    "summary": "Sincroniza clientes (res.partner) do Odoo para o PHC CSWeb via Web Service SOAP",
    "description": """
PHC Connector (clientes)
========================

Objetivo de negócio
-------------------
A Triplex fatura/opera também no PHC CSWeb. Os clientes têm de existir e estar atualizados
no PHC. Este módulo cria/atualiza automaticamente o cliente no PHC quando se cria/edita o
parceiro no Odoo, evitando dupla introdução de dados.

Pré-requisitos
--------------
- Módulos: `base`, `account`.
- Em Definições da Empresa (res.company): configurar PHC WS URL (`phc_api_base_url`),
  utilizador (`phc_api_user`) e password (`phc_api_password`).
- Acesso de rede ao Web Service SOAP do PHC e credenciais válidas.
- Campos PHC no parceiro: código de país, vendedor PHC, tabela de preços, etc. (o módulo
  cria-os por hook se faltarem — ver Pontos de atenção).

Como funciona
-------------
- `res.partner`: campos PHC (limites de tamanho em PHC_LIMITS), flag `is_phc_synced`
  (False = criar no próximo save; True = atualizar a cada save) e `phc_last_response` (debug).
- Ao gravar o parceiro, envia um pedido SOAP ao PHC: script `CriaCL` (criar) ou `UpdateCL`
  (atualizar). Trata validações (NIF/VAT, exceções de duplicado, limites de campos).
- `res.company`/`res.config.settings`: guardam as credenciais/endpoint do PHC.
- `hooks.py`: garante (por SQL e por ir.model.fields) que as colunas/campos PHC do parceiro
  existem, mesmo sem os campos Studio. Há migrações em migrations/.

Passo a passo de utilização
---------------------------
1. Em Definições > Empresa, preencher URL/utilizador/password do PHC.
2. Preencher nos clientes os campos PHC obrigatórios (país, vendedor, tabela de preços).
3. Gravar o cliente — é criado no PHC (is_phc_synced passa a True); gravações seguintes atualizam.
4. Em caso de erro, consultar "Última resposta PHC" no parceiro.

Exemplo prático
---------------
Criar o cliente "Móveis Silva" com NIF e código de país PT -> ao gravar, o conector chama
`CriaCL` no PHC e o cliente fica criado lá; uma alteração de morada depois dispara `UpdateCL`.

FAQ / Resolução de problemas
----------------------------
- P: Dá erro a pedir para configurar campos da empresa.
  R: Falta o URL/utilizador/password do PHC nas Definições da Empresa.
- P: "não pode alterar o NIF".
  R: O PHC bloqueia alteração de NIF de clientes já existentes (PHC_VAT_LOCK_MSG_SNIPPET).
- P: NIF duplicado.
  R: Há exceções permitidas (999999990, "SEM NIF"); restantes duplicados são recusados.
- P: Campo demasiado longo.
  R: O PHC tem limites por campo (PHC_LIMITS); o conector valida/trunca conforme aplicável.

Pontos de atenção (FACTOS OBSERVADOS)
-------------------------------------
- O `__manifest__.py` NÃO declara `pre_init_hook`/`post_init_hook`, apesar de existirem em
  hooks.py. Tal como está, esses hooks não são executados automaticamente na instalação —
  rever se a criação de colunas/campos PHC é necessária via hook.
- `models/res_partner_old.py` NÃO é importado (não está em models/__init__.py) — é código
  morto, mantido por histórico.
- Comunicação SOAP com `verify_ssl=False` em partes do fluxo (ignora verificação TLS).
- É a base do módulo `pg_phc_api_integration` (faturas e guias de transporte).
""",
    "author": "Parâmetro Global",
    "license": "LGPL-3",
    "depends": [
        "base",
        "account",
    ],
    "data": [
        "views/res_partner_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
}
