{
    'name': 'Transferencia Interna',
    'version': '18.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Gerenciamento de transferencias internas entre diarios',
    'description': """
        Modulo para gestao de transferencias internas entre diarios contabilisticos.
        Recriado a partir da estrutura da base de dados.
    """,
    'author': 'Anorak FranceInnovactive',
    'depends': ['account', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/internal_transfer_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
