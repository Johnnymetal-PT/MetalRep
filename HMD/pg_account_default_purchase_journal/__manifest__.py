# -*- coding: utf-8 -*-
{
    "name": "PG Account Default Purchase Journal",
    "summary": "Força o diário por defeito das faturas de fornecedor (configurável por empresa).",
    "version": "18.0.1.0.0",
    "author": "Parametro Global",
    "website": "https://www.parametroglobal.com",
    "category": "Accounting",
    "license": "LGPL-3",
    "description": """
PG Account Default Purchase Journal (HMD)
=========================================

a) Objetivo de negócio
----------------------
Ao criar faturas de fornecedor (manualmente ou a partir de um pedido de
compra), o Odoo escolhia automaticamente o diário "Custos com Pessoal" em
vez de "Faturas de Fornecedor". O default standard depende da ordenação
por `sequence` dos diários de compra e não era controlável de forma fiável
pela interface (nem por `ir.default`, nem por reordenação de sequência).

Este módulo permite fixar, por empresa, o diário de compra que deve ser o
default das faturas de fornecedor.

b) Como funciona (técnico)
--------------------------
1. `res.company.pg_default_purchase_journal_id` (Many2one a
   `account.journal`, domínio `type = purchase`): diário a usar por defeito.
2. `res.config.settings`: expõe o campo em Contabilidade > Definições,
   bloco "Faturas de Fornecedor".
3. `account.move._search_default_journal` (override): no caminho de
   *default* dos documentos de compra (`in_invoice`/`in_refund`), devolve o
   diário configurado em vez do default standard.
   - Só atua quando os tipos válidos do movimento incluem `purchase`.
   - Só usa o diário configurado se o utilizador atual lhe puder aceder
     (respeita as regras de registo / whitelist de `pg_account_journal_access`);
     caso contrário, mantém o default standard para não criar AccessError.
   - Não interfere com a escolha manual do utilizador: `_compute_journal_id`
     só recalcula quando o diário atual é de tipo inválido.

c) Configuração
---------------
Contabilidade > Definições > "Faturas de Fornecedor" > "Diário por defeito"
> selecionar "Faturas de Fornecedor" > Guardar.

d) Pontos de atenção
--------------------
- Se o campo ficar vazio, o comportamento volta ao standard do Odoo.
- Em upgrade (ex.: Odoo 19), validar que `_search_default_journal` mantém a
  mesma assinatura e ponto de chamada.
""",
    "depends": ["account"],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "application": False,
}
