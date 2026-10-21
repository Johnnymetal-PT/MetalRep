{
    "name": "PG Purchases from Sales Order",
    "version": "19.0.1.0.0",
    "depends": ["sale", "purchase"],
    "author": "Parametro Global",
    "category": "Sales",
    "summary": "Gera Ordens de Compra a partir de uma Encomenda de Venda confirmada, agrupando por fornecedor.",
    "description": """
PG Purchases from Sales Order
=============================

a) Objetivo de negocio
----------------------
Permitir ao operador comercial, a partir de uma Encomenda de Venda confirmada,
gerar manualmente as Ordens de Compra correspondentes aos produtos vendidos,
agrupando por fornecedor. Tipico quando se trabalha em logica MTO/encomenda
sem auto procurement, ou quando se quer revisao humana antes de chegar a
PO.

A SO fica ligada as POs criadas via `procurement.group`, com:
- smart button "Ordens de Compra" no form da SO;
- proteccao para nao re-criar POs por engano (mostra wizard de confirmacao).

b) Pre-requisitos
-----------------
- Modulos: `sale`, `purchase`.
- Cada produto da SO tem de ter pelo menos um `seller_ids` (fornecedor)
  definido; caso contrario o gerador rebenta com UserError indicando o
  produto.
- A SO tem de estar em estado `sale`.

c) Como funciona
----------------
- `models/sale_order.py`:
  - `sale.order` ganha:
    - `procurement_group_id` (Many2one - ligacao a `procurement.group`).
    - `purchase_created` (Boolean - flag para nao gerar duas vezes sem
      confirmacao).
    - `purchase_order_ids` (Many2many computed via group_id) +
      `purchase_order_count` para o smart button.
    - `internal_transfer_ids` (One2many computed via `origin` -> pickings
      internal) - util quando convive com [[pg_dynamic_mto_transfer]].
  - `open_generate_purchase_po_wizard`:
    - Se a SO ainda nao gerou POs, chama `action_generate_purchase_orders`
      directamente.
    - Caso ja tenha gerado, abre o wizard de confirmacao (evita duplicar).
  - `action_generate_purchase_orders`:
    1. Agrupa linhas por fornecedor (primeiro `seller_ids[0].partner_id`).
    2. Cria uma `purchase.order` por fornecedor com:
       - `partner_id` = vendor.
       - `origin` = nome da SO.
       - `origin_sale_order_id` = a SO (campo custom em PO).
       - `group_id` = procurement_group_id (compartilhado).
       - `order_line` com os produtos da SO (qty, uom, standard_price,
         date_planned = hoje).
    3. Marca `purchase_created = True` e abre o tree das POs criadas.
  - Adiciona accao `action_open_purchase_orders` para o smart button.
- `models/sale_order.py` tambem extende:
  - `purchase.order.origin_sale_order_id` (Many2one para SO).
  - `sale.order.line.product_variant_desc` (campo computed vazio - parece
    placeholder).
- `wizards/generate_purchase_wizard.py`:
  - `generate.purchase.wizard` (TransientModel) com `sale_order_id`. O
    metodo `confirm_generate_po` chama o gerador.

d) Passo a passo de utilizacao
------------------------------
1. Confirmar a SO.
2. Clicar no botao "Gerar Compras" (registado em
   `views/sale_order_view.xml`).
3. Se ja foi gerado anteriormente, surge wizard a perguntar se quer
   regerar. Caso contrario, gera imediatamente.
4. O sistema cria 1 PO por fornecedor com as respetivas linhas e abre o
   tree das POs criadas.
5. No form da SO o smart button "Ordens de Compra" passa a mostrar a
   contagem.

e) Exemplo pratico
------------------
- SO #1234 com 3 produtos:
  - Cadeira (fornecedor Kave Home)
  - Mesa (fornecedor Kave Home)
  - Tapete (fornecedor Iberica Tapetes)
- Acao "Gerar Compras":
  - Cria PO Kave Home com 2 linhas.
  - Cria PO Iberica Tapetes com 1 linha.
- SO #1234.purchase_created = True. Smart button mostra "2".

f) FAQ / Resolucao de problemas
-------------------------------
- "UserError: Nenhum fornecedor definido para o produto 'X'":
  Configurar `seller_ids` no produto (Compras / Vendor info).
- "UserError: So pode gerar ordens de compra para encomendas confirmadas":
  A SO tem de estar em estado `sale`. Em draft/sent nao gera.
- "O smart button mostra 0 mas eu vejo POs no Odoo":
  As POs sao listadas via `procurement_group_id`. Se a SO nao tiver
  `procurement_group_id` preenchido (criada antes do modulo, ou sem MTO),
  o smart button nao encontra. [PONTO POR VALIDAR] estrategia para SOs
  legacy.
- "Gerei duas vezes e tenho POs duplicadas":
  Apos `purchase_created=True` o sistema mostra wizard de confirmacao. Se
  for confirmado novamente, gera novamente sem apagar as anteriores.
  Recomenda-se cancelar manualmente as POs duplicadas antes de regerar.

g) Pontos de atencao
--------------------
- `price_unit` da PO line e o `standard_price` do produto. Se o preco de
  fornecedor for diferente, fica errado e o operador tem de corrigir.
- O campo `product_variant_desc` em `sale.order.line` esta a ser computed
  com string vazia; aparente placeholder mantido para nao quebrar uma
  vista. [PONTO POR VALIDAR] se pode ser removido.
- `internal_transfer_ids` partilha logica com [[pg_dynamic_mto_transfer]]
  mas com lookup diferente (por `origin == sale.name`); convem alinhar para
  evitar discrepancias.
- Wizard `generate.purchase.wizard` so confirma; nao oferece opcao para
  "fazer diff" ou regenerar parcialmente.
    """,
    "data": [
        "views/sale_order_view.xml",
        "views/actions.xml",
        "views/generate_purchase_wizard_view.xml",
        "security/ir.model.access.csv"
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
