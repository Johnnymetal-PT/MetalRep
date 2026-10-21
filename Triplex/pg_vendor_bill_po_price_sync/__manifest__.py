# -*- coding: utf-8 -*-
{
    'name': 'pg Vendor Bill → PO Price Sync',
    'version': '17.0.2.0.0',
    'summary': 'Propaga preço e descontos editados numa linha de Fatura de Fornecedor para a linha da Ordem de Compra',
    'description': """
pg Vendor Bill → PO Price Sync
==============================

Objetivo de negócio
-------------------
A Fatura de Fornecedor é preenchida automaticamente a partir da Ordem de Compra (PO).
Quando se ajusta o preço (price_unit) ou o desconto numa linha da fatura, este módulo
escreve esses valores na linha da PO correspondente, mantendo a PO como reflexo do que
foi efetivamente faturado.

Como funciona
-------------
- A ligação usada é a `purchase_line_id` da `account.move.line` (criada pelo módulo
  standard `purchase` quando a fatura é gerada a partir da PO).
- Ao gravar uma alteração de `price_unit`, `discount` (ou `sh_multi_discount`) numa linha
  de fatura de fornecedor (`in_invoice`/`in_refund`) com `purchase_line_id`, os valores são
  escritos na linha da PO.
- Só escreve os campos que diferem e usa um contexto-guarda (`pg_skip_po_price_sync`) para
  evitar reentrância.

Âmbito / notas
--------------
- Propaga **preço unitário** e **desconto**: o `discount` standard (que determina o total)
  e, se o módulo `pg_multi_discount` estiver instalado, também a cascata `sh_multi_discount`.
  Impostos não são propagados.
- O utilizador que edita a fatura tem de ter permissão para escrever na PO; caso contrário
  a gravação falha com erro de acesso (não usa `sudo`).
- Aplica-se a faturas e notas de crédito de fornecedor.
""",
    'category': 'Accounting',
    'author': 'Parametro Global',
    'license': 'LGPL-3',

    'depends': ['purchase'],

    'data': [],

    'installable': True,
    'application': False,
}
