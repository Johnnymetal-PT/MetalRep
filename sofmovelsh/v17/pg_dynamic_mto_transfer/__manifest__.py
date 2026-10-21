{
    "name": "PG Dynamic MTO Transfer",
    "version": "17.0.1.0.0",
    "depends": ["stock", "purchase", "sale_stock"],
    "author": "Parametro Global",
    "category": "Inventory",
    "summary": "Substitui MTO standard por logica de transferencia inter-warehouses com PO como fallback.",
    "description": """
PG Dynamic MTO Transfer
=======================

a) Objetivo de negocio
----------------------
A logica MTO standard do Odoo dispara sempre uma PO ao fornecedor quando ha
procurement. Para Sofmovel (que tem warehouses BRA, SEI e FRE), pretende-se
primeiro:
1. Usar stock livre no warehouse alvo.
2. Se nao chegar, fazer transferencia interna a partir de outro warehouse
   pela lista de prioridades (cada warehouse tem a sua).
3. So fazer PO ao fornecedor se mesmo assim restar quantidade.

E despois materializar (ou ajustar) a delivery no mesmo `procurement.group`.

b) Pre-requisitos
-----------------
- Modulos: `stock`, `purchase`, `sale_stock`.
- Warehouses com `code` exatamente em "BRA", "SEI" e "FRE".
- Lista de prioridades (hardcoded em `stock_rule.py`):
  - BRA -> [FRE, SEI]
  - SEI -> [FRE, BRA]
  - FRE -> [BRA, SEI]
- Picking type `internal` por warehouse (auto-criado pelo Odoo, normalmente
  existe).
- Rota standard `stock.route_warehouse0_mto` (existe por defeito).

c) Como funciona
----------------
- `models/stock_rule.py` faz override de `_run_pull`:
  1. Para cada `(procurement, rule)`:
     - Step 1: Usa `free_qty` no warehouse alvo (so quantidade livre, nao
       reservada).
     - Step 2: Itera pelos warehouses alternativos segundo a prioridade.
       Para cada um:
       - Le `free_qty`.
       - Calcula `transfer_qty` (minimo entre free e o que falta).
       - Cria `stock.picking` do tipo `internal` no warehouse de origem,
         destino = warehouse alvo, com uma move por produto.
       - Anexa `sale_id`, `partner_id` (se houver SO origem) e `group_id`
         do procurement.
       - `message_post` no picking criado.
     - Step 3: Se ainda faltar quantidade, chama `super()._run_pull` com um
       procurement reconstruido (mesma rule, novo qty), o que dispara a
       criacao da PO segundo a rota de compra.
     - Step 4: Materializa/patch da delivery (`outgoing` picking) com a
       quantidade correta:
       - Procura outgoing existente para o `group_id`.
       - Se existir move para o produto: patch direto da `product_uom_qty`.
       - Senao: cria via `super()._run_pull` removendo a rota MTO da
         lista (`route_ids` filtrada) e patch a seguir.
- `models/sale_order.py` adiciona `internal_transfer_ids` (One2many
  computed sem store) e a accao `action_view_internal_transfers` para
  abrir o tree de transferencias internas a partir da SO.

d) Passo a passo de utilizacao
------------------------------
1. Confirmar codes dos warehouses e prioridades.
2. Criar SO com produto e rota MTO no warehouse BRA (por exemplo).
3. Confirmar a SO. O modulo:
   - Verifica stock em BRA, depois em FRE, depois em SEI.
   - Cria transferencias internas necessarias.
   - Se ainda faltar, dispara PO.
   - Cria/patch a delivery final para a SO.
4. No form da SO, smart button "Internal Transfers" mostra os pickings
   internos criados.

e) Exemplo pratico
------------------
- SO com 10 un do produto X, warehouse alvo BRA.
- Stock livre: BRA=2, FRE=7, SEI=1.
- O modulo cria:
  - Transferencia interna FRE -> BRA de 5 un (limitado pelo que falta).
  - Transferencia interna SEI -> BRA de 1 un.
  - PO de 2 un ao fornecedor (10 - 2 - 5 - 1 = 2).
- Delivery sai com 10 un assim que houver stock suficiente.

f) FAQ / Resolucao de problemas
-------------------------------
- "Erro: No internal transfer type found for warehouse 'XYZ'":
  O warehouse alternativo nao tem picking type internal. Verificar config
  do warehouse (gera-se por defeito).
- "Erro: Alternate warehouse 'XYZ' not found":
  Codes nao batem com BRA/SEI/FRE. Validar codes nas warehouses.
- "PO esta a ser disparada antes das transferencias internas":
  Verificar logs com tag "[MTO LOGIC]" - mostram o passo a passo da decisao
  por procurement.
- "Delivery duplicada":
  O Step 4 procura outgoing existente antes de chamar super; se houver
  divergencia entre `group_id` na SO e nas pickings, pode criar duplicado.

g) Pontos de atencao
--------------------
- A lista de prioridades esta hardcoded por code de warehouse. Em
  ambientes com outros codes (ou novos warehouses) tem de ser atualizada.
- O override sobrescreve completamente `_run_pull` para procurements MTO -
  pode entrar em conflito com outros modulos que tambem o redefinam.
- Step 4 remove a rota MTO de `route_ids` antes de chamar super para criar
  a delivery; assume que a rota MTO esta presente (ref `stock.route_warehouse0_mto`).
- Os logs sao bastante verbosos com emojis ([MTO LOGIC] ...); uteis para
  debug, mas considerar baixar verbosity em producao.
- Os comentarios `// FIXED` no codigo referem-se a bugs corrigidos durante
  o desenvolvimento; mantidos para registo historico.
    """,
    "installable": True,
    "auto_install": False,
    "data": [
        "views/sale_order_view.xml"
    ],
}
