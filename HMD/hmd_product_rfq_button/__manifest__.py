# -*- coding: utf-8 -*-
{
    'name': 'HMD Product RFQ Button',
    'version': '18.0.1.5.0',
    'summary': 'Botao smart "RFQs" em produto/variante - lista todos os RFQs em qualquer estado.',
    'description': """
HMD Product RFQ Button
======================

a) Objetivo de negocio
----------------------
Quando o operador HMD quer rapidamente ver QUAIS pedidos de cotacao
(RFQ) e ordens de compra envolvem um produto, o standard so mostra POs
confirmadas (state in ['purchase','done']). Este modulo conta e expoe
TODOS os `purchase.order` (em qualquer estado) ligados ao produto, e
abre a list ao clicar no botao smart.

b) Pre-requisitos
-----------------
- Odoo 18.0 Enterprise (versao ativa em PG_CONTEXT.md).
- Modulos `product` e `purchase`.

c) Como funciona (tecnico)
--------------------------
1. `product.template` (`models/product_template.py`):
   - `rfq_purchase_order_count`: Integer computed (compute_sudo).
     Usa SQL raw (JOIN purchase_order_line + product_product) para
     contar POs distintas por template. Eficiente em batch.
   - `action_view_rfq_purchase_orders`: le a acao standard
     `purchase.purchase_rfq`, restringe `domain` aos product_ids do
     template, e LIMPA os filtros `search_default_*` do contexto (o
     standard tem `search_default_rfq` que esconde POs confirmadas -
     queremos ver todas).

2. `product.product` (`models/product_product.py`): mesmo
   comportamento mas ao nivel da variante (`read_group` em vez de
   SQL raw).

3. View (`views/product_views.xml`): adiciona um botão smart
   "RFQs" (ícone fa-shopping-cart) ao button_box do template e da
   variante. O botão usa `type="object"` e chama diretamente
   `action_view_rfq_purchase_orders()` no registo atual, sem indireção
   por `ir.actions.server` (evita a leitura do campo `code`, restrito a
   `base.group_system`, que partia o botão para utilizadores sem esse
   grupo).

d) Passo a passo de utilizacao
------------------------------
1. Instalar `hmd_product_rfq_button`.
2. Inventario > Artigos > abrir um produto template.
3. No topo aparece botao "RFQs" com a contagem.
4. Clicar abre a list de purchase.order com todos os estados
   (incluindo cancelados).

e) Exemplo pratico
------------------
Produto "Tecido cima" tem:
  - PO P01 (state=draft) com linha desse produto.
  - PO P02 (state=purchase) com linha desse produto.
  - PO P03 (state=cancel) com linha desse produto.

`rfq_purchase_order_count` = 3. Botao abre lista com P01, P02, P03.
O standard ("Purchases" smart button) so mostraria 1 (P02).

f) FAQ / Resolucao de problemas
-------------------------------
P: O botao mostra 0 mas eu vejo POs com o produto. Porque?
R: A query usa `purchase_order_line.product_id` -> `product_product`
   -> `product_tmpl_id`. Se a PO foi criada sem product_id (so com
   nome livre), nao conta. Validar a linha.

P: O numero esta diferente do standard ("Purchases"). Esta correto?
R: Sim - aqui contam-se POs em todos os estados, o standard so conta
   confirmadas. Diferenca esperada.

g) Pontos de atencao / avisos
-----------------------------
- SQL raw no template - se for renomeada alguma tabela em upgrade
  para Odoo 19, falha de schema. Reavaliar.
- O `read()[0]` da acao do standard pressupoe que ela existe e e
  unica. Aceitavel para uma acao standard `purchase.purchase_rfq`.
- Limpeza de `search_default_*` e intencional: o standard injeta
  defaults que filtram so RFQs em rascunho.
""",
    'author': 'Parametro Global',
    'website': 'https://parametro.global',
    'license': 'LGPL-3',
    'depends': ['product', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
    ],
    'installable': True,
    'application': False,
}
