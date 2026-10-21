# -*- coding: utf-8 -*-
{
    'name': 'MH — Conta de Devoluções de Compras',
    'version': '18.0.1.0.0',
    'summary': 'Encaminha as devoluções a fornecedor (stock + nota de crédito) '
               'para uma conta própria (ex.: 217), mantendo o inventário perpétuo.',
    'description': """
MH — Conta de Devoluções de Compras
===================================
Nas **devoluções a fornecedor**, o Odoo (perpétuo) lança a contrapartida na
**conta de entrada de stock** (a mesma das compras). Este módulo permite definir
uma **conta de devoluções própria** (ex.: 217) na **categoria de produto**, e
encaminha **os dois lados** para essa conta — mantendo a reconciliação e o
inventário perpétuo intactos:

- **Lado do stock** (picking de devolução): override do ``_get_src_account`` —
  quando o movimento é uma saída para fornecedor (``_is_returned('out')``), a
  contrapartida usa a conta de devoluções da categoria.
- **Lado da nota de crédito** (``in_refund``): override do ``_compute_account_id``
  — quando a NC é uma devolução de mercadoria (flag ``mh_purchase_return``,
  automático quando ligada a um picking de devolução, ou manual), a linha do
  produto lança na conta de devoluções.

Só afeta **devoluções de compra**: as compras normais, vendas e devoluções de
venda ficam intactas.
""",
    'author': 'Make It Happen',
    'website': 'https://mhc.co.mz',
    'category': 'Accounting/Accounting',
    'license': 'LGPL-3',
    'depends': ['stock_account', 'account', 'mh_return_credit_note'],
    'data': [
        'views/product_category_views.xml',
    ],
    'installable': True,
}
