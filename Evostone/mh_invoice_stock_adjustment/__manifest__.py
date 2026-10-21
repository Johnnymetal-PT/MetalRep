{
    'name': 'MH Acerto Stock na Factura',
    'version': '18.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Acerto automático de diferenças entre recepção e facturação',
    'description': """
MH Acerto Stock na Factura
==========================

Quando se valida uma factura de fornecedor, pode haver diferença entre
a quantidade recebida (picking) e a quantidade facturada.

Cenários:
- Surplus (recebeu mais do que facturou): Ganho de existências → conta 789003
- Deficit (recebeu menos do que facturou): Acerto na factura + lançamento STJ

Lógica:
- Surplus: STJ → Débito 211xx / Crédito 789003
- Deficit: STJ → Débito conta deficit / Crédito 211xx (factura não alterada, quebra registada)

Conta deficit determinada por:
1. Artigo manual com acerto_de_stock=True → conta do artigo
2. Settings → Contabilidade → Acerto de Stock → Conta Deficit
    """,
    'author': 'MH',
    'website': '',
    'depends': [
        'account',
        'purchase_stock',
        'stock_account',
    ],
    'data': [
        'views/product_template_views.xml',
        'views/account_move_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
