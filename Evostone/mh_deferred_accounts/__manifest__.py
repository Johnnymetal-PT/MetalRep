{
    'name': 'MH Multi Deferred Accounts',
    'version': '18.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Contas de diferimento específicas por produto',
    'description': """
Permite definir contas de diferimento específicas por produto, sobrepondo o default da empresa.
Campos adicionados em product.template:
- Deferred Expense Account
- Deferred Revenue Account
Se o produto não tem conta configurada, usa o default da empresa (fallback).
    """,
    'author': 'Make It Happen',
    'depends': ['account_accountant'],
    'data': [
        'views/product_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
