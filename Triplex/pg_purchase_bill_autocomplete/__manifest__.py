# -*- coding: utf-8 -*-
{
    'name': 'pg Purchase Bill Auto-Complete (linhas a 0 €)',
    'version': '17.0.1.0.0',
    'summary': 'Mantém no Auto-Complete da fatura as compras com linhas a 0 € ainda por faturar',
    'description': """
pg Purchase Bill Auto-Complete (linhas a 0 €)
=============================================

Problema
--------
Nesta base o preço da compra é atualizado a partir da fatura de fornecedor
(ver `pg_vendor_bill_po_price_sync`). Uma linha pode por isso ficar na compra a 0 €,
sem receção, à espera da fatura. Quando as restantes linhas já foram faturadas, o Odoo
marca a compra como `invoiced` e retira-a da lista do Auto-Complete da fatura
(`purchase.bill.union`), pelo que a fatura seguinte não consegue ir buscar a compra.

O que faz
---------
1. `purchase.bill.union`: além das compras `to invoice` / `no`, inclui as compras
   confirmadas que tenham pelo menos uma linha a 0 € com quantidade e ainda sem qualquer
   faturação (`qty_invoiced = 0`).
2. `purchase.order.line._prepare_account_move_line`: nessas linhas a 0 €, a linha da fatura
   vem com a quantidade encomendada (e não 0, que é o `qty_to_invoice` quando o produto
   fatura por quantidade recebida), para o utilizador só ter de indicar o preço. O preço é
   depois propagado para a compra por `pg_vendor_bill_po_price_sync`.

Âmbito / notas
--------------
- Não altera o `invoice_status` da compra nem a política de faturação dos produtos.
- Linhas a 0 € intencionais (amostras, ofertas) mantêm a compra visível no Auto-Complete
  até serem faturadas ou até a linha ter preço.
- A vista SQL é recriada no `init()`: instalar/atualizar o módulo, ou o `purchase`, reaplica-a.
""",
    'category': 'Inventory/Purchase',
    'author': 'Parametro Global',
    'license': 'LGPL-3',

    'depends': ['purchase'],

    'data': [],

    'installable': True,
    'application': False,
}
