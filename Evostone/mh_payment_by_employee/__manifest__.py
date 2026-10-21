{
    'name': 'MH Pagamentos por Funcionários',
    'version': '18.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Automatiza pagamentos de facturas de fornecedor por funcionários (PGF)',
    'description': """
        Quando uma factura de fornecedor é paga por um funcionário,
        este módulo permite transferir a dívida do fornecedor para o funcionário
        com um clique, criando automaticamente o lançamento PGF e reconciliando a factura.
    """,
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/payment_by_employee_wizard_views.xml',
        'views/account_move_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
}
