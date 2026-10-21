# -*- coding: utf-8 -*-
{
    "name": "PG Sale Advance Payment Access",
    "summary": "Permite ver adiantamentos no orcamento sem expor o diario "
               "restrito por pg_account_journal_access.",
    "version": "18.0.1.0.0",
    "author": "Parametro Global",
    "website": "https://parametro.global",
    "category": "Sales",
    "license": "LGPL-3",
    "description": """
PG Sale Advance Payment Access (HMD)
====================================

a) Objetivo de negocio
----------------------
O modulo `pg_account_journal_access` instala regras `ir.rule` GLOBAIS
(sem grupo) em `account.journal`, `account.move` e `account.move.line`
que escondem diarios sensiveis a quem nao esteja na whitelist do
diario. Isto e intencional para diarios de banco/numerario sensiveis.

Efeito colateral: o modulo `sale_advance_payment` mostra os
adiantamentos (`account.payment`) na aba "Payment advances" do
orcamento, usando a vista de lista/formulario STANDARD do pagamento,
que inclui a coluna `journal_id`. Ao abrir um orcamento com um
adiantamento registado num diario que o utilizador nao pode ler
(ex.: "Millennium BCP"), o Odoo tenta ler `account.journal` -> a regra
global dispara -> `AccessError` e o orcamento nao abre.

Decisao consultiva (HMD): o diario deve continuar OCULTO, mas o
vendedor/faturacao deve poder abrir o orcamento e ver que existe um
adiantamento (data, referencia, montante, estado), SEM aceder ao
diario nem ao ledger.

b) Como funciona (tecnico)
--------------------------
FACTO OBSERVADO (vendor/odoo_src 18.0,
`addons/account/models/account_payment.py`): os campos `date`, `name`,
`partner_id`, `amount`, `currency_id` e `state` de `account.payment`
sao STORED no proprio pagamento e NAO passam por `account.move`. A
unica coluna da vista de pagamento que forca a leitura de
`account.journal` e `journal_id`
(`addons/account/views/account_payment_view.xml`, linha 20).

Logo, NAO e preciso `sudo` nem alterar seguranca. Basta apresentar os
adiantamentos com vistas proprias `pg_` que omitem `journal_id` (e
qualquer campo que toque em `move`/`journal`):

1. `views/pg_account_payment_views.xml`:
   - `view_pg_account_payment_tree`: lista read-only de `account.payment`
     com data, numero, cliente, montante e estado. Sem `journal_id`.
   - `view_pg_account_payment_form`: formulario read-only minimo com os
     mesmos campos stored. Sem `journal_id`, `move_id`, stat buttons.

2. `views/pg_sale_order_views.xml`:
   - herda a vista de orcamento de `sale_advance_payment` e redireciona
     o `context` do campo `account_payment_ids` para as vistas `pg_`
     acima. ATENCAO: em Odoo 18 a chave correta e `list_view_ref`
     (o `tree`->`list` foi renomeado em v17/18); `tree_view_ref` e
     ignorado pelo webclient. Mantemos ambas as chaves +
     `form_view_ref` por compatibilidade.

Resultado: o orcamento abre para todos os utilizadores internos; o
diario restrito nunca e lido a partir da venda. Quem tiver acesso ao
diario continua a ver o detalhe completo via Contabilidade.

c) Pontos de atencao / avisos
-----------------------------
- Se uma futura versao de `sale_advance_payment` renomear o campo
  `account_payment_ids` ou a sua vista (`view_order_form`), atualizar
  o `inherit_id` / o `position="attributes"`.
- Em upgrade Odoo 19, revalidar os campos stored de `account.payment`
  (`date`, `name`, `amount`, `state`) e a estrutura da vista
  `account.view_account_payment_tree`.
- Nao remove a confidencialidade: apenas evita a leitura do diario a
  partir do orcamento. As regras de `pg_account_journal_access`
  mantem-se inalteradas.
""",
    "depends": [
        "sale_advance_payment",
        "account",
    ],
    "data": [
        "views/pg_account_payment_views.xml",
        "views/pg_sale_order_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
