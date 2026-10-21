{
    'name': 'PG B2B Discounts',
    'version': '1.0',
    'summary': 'Manage discount tiers for B2B partners based on total spendings.',
    'category': 'Sales',
    'author': 'Your Name',
    'depends': ['sale', 'account'],
    'data': [
        'data/pg_b2b_discount_cron.xml',
        #'views/templates.xml',  # New file for templates
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
