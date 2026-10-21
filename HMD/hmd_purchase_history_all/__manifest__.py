{
    "name": "HMD Purchase History All States",
    "version": "18.0.1.0.0",
    "summary": "Historico de compras do produto: mostra POs em TODOS os estados, recriando a view SQL.",
    "category": "Purchase",
    "author": "HMD / Parametro Global",
    "website": "https://www.hmd.pt",
    "depends": ["purchase"],
    "data": [
        "views/purchase_history_tree_view.xml",
        "views/product_views.xml",
    ],
    "license": "LGPL-3",
    "description": """
HMD Purchase History All States (HMD)
=====================================

a) Objetivo de negocio
----------------------
O smart button "Purchases" standard no produto mostra apenas POs em
estados `purchase` ou `done`. Para a HMD interessa ver TODAS as POs
ligadas ao produto (incluindo `draft`, `sent`, `to approve`, `cancel`)
para nao perder historico nem RFQs em pipeline. Este modulo:
  - relaxa o filtro de estado na view SQL `purchase.history.list` em
    runtime (reescreve o SQL no schema);
  - sanitiza dominio + contexto das acoes `action_view_po` (em
    `product.template`, `product.product` e `product.supplierinfo`)
    para remover restricoes de estado;
  - adiciona um botao smart "RFQs" com contagem distinta de POs
    ligadas ao produto.

b) Pre-requisitos
-----------------
- Odoo 18.0 Enterprise (versao ativa em PG_CONTEXT.md).
- Modulo `purchase`.

c) Como funciona (tecnico)
--------------------------
1. `purchase.history.list._relax_state_filter` (em
   `models/purchase_history_list.py`):
   - Chamado no `init()` do modelo - corre no instalar/atualizar.
   - Le o SQL atual da view via `pg_get_viewdef`.
   - Procura por padroes regex que correspondem a filtros sobre o
     campo `state` (COALESCE/IN, ==, !=, etc.) e substitui por TRUE.
   - Recria a view com `CREATE OR REPLACE VIEW`.
   - SE nao encontrar nenhum filtro de estado, deixa a view
     inalterada (warning no log).

2. `_sanitize_purchase_history_action`
   (em `models/product_template.py`):
   - Parser de dominio em arvore (& / | / ! / leaf / const).
   - Identifica termos cujo campo contem "state" e remove-os
     (substitui por const True).
   - Simplifica a arvore (eliminar `True AND X -> X`, etc.).
   - Devolve o dominio limpo em string ou lista, conforme o input.

3. `product.template.action_view_po` e
   `product.product.action_view_po` overrides: chamam `super()` e
   passam o resultado pelo sanitizador.

4. `product.supplierinfo.action_purchase_history` override: idem
   para o historico ao nivel do fornecedor.

5. View XML (`views/purchase_history_tree_view.xml`): substitui a
   `<list>` standard por uma versao que mostra `date_approve`,
   `partner_id`, `company_id`, `product_uom_qty`, `price_unit`,
   `price_subtotal` e estado opcional.

6. Smart button RFQs (`views/product_views.xml`):
   - `hmd_purchase_rfq_count` em `product.template` e
     `product.product` - read_group por `product_id` e count_distinct
     de `order_id`.
   - `action_view_rfq_purchase_orders` (em
     `_prepare_purchase_orders_action`): le a acao standard
     `purchase.purchase_form_action`, anula os `search_default_*` que
     filtrariam por estado, restringe `domain` aos product_ids.

d) Passo a passo de utilizacao
------------------------------
1. Instalar `hmd_purchase_history_all`. O install corre o
   `_relax_state_filter` que recria a SQL view do historico.
2. Inventario > Artigos > abrir um produto. O botao "Purchases"
   standard passa a mostrar todas as POs. Adicionalmente aparece o
   botao smart "RFQs" com a contagem.
3. Clicar abre a list com ordering por `order_id asc`.

e) Exemplo pratico
------------------
Produto "Tecido cima" tem POs:
  - P01 draft, P02 purchase, P03 done, P04 cancel.
Standard: 2 (P02, P03).
Com este modulo: 4 (todas).

f) FAQ / Resolucao de problemas
-------------------------------
P: Apos instalar, o historico ainda nao mostra as draft. Resolver?
R: Verificar que o `_relax_state_filter` correu (procurar no log
   "Recreated purchase history view"). Se nao correu, atualizar o
   modulo (faz `init()` re-executar).

P: O smart button RFQs mostra um numero diferente do
   `hmd_product_rfq_button`. Porque?
R: Os dois modulos contam o mesmo (POs distintas) mas usam queries
   ligeiramente diferentes (SQL raw vs read_group). Em pratica devem
   bater certo. Se nao baterem, verificar produtos com PO sem
   product_id.

P: Em upgrade Odoo 19, o regex que reescreve a view pode falhar?
R: Sim. O SQL da view standard pode mudar de forma. Se o padrao nao
   bater, o `_relax_state_filter` deixa um warning e a view fica
   intacta - sem regressao funcional, mas o filtro nao e relaxado.
   Validar regex contra a nova versao.

g) Pontos de atencao / avisos
-----------------------------
- Reescrita do SQL view e operacao baixa: usa `CREATE OR REPLACE
  VIEW`. Roda no `init()`. Em ambientes multi-DB, atencao.
- Os regex que detetam `state IN (...)` sao heuristicos. Em mudanca
  de schema, o `_logger.warning` indica que ficou inalterado.
- Como o standard `action_view_po` muda entre micro-versoes, o
  sanitizador e robusto a dominio em string OU em lista.
- O ACL e seguranca padrao - o utilizador continua a precisar de
  ver POs para que o historico aparecer.
""",
    "installable": True,
    "application": False,
}
