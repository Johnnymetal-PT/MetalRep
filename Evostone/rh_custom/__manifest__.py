{
    'name': 'Custom HR Pemaro',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Automatizacoes personalizadas de RH',
    'description': """
        Modulo com customizacoes de RH para Pemaro.
        Recriado a partir da estrutura da base de dados.
    """,
    'author': 'Seu Nome ou Empresa',
    'depends': ['hr_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'views/payslip_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
