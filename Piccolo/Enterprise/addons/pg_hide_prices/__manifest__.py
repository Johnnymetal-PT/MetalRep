{
    'name': 'PG Hide Product Prices for Non-Logged Users',
    'version': '1.0',
    'summary': 'Hide product prices on product pages for non-logged-in users',
    'author': 'Your Name',
    'category': 'Website',
    'depends': ['website_sale'],
    'data': [
        'views/website_templates.xml',
        'security/ir.model.access.csv',
    	'security/ir_rule.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'pg_hide_prices/static/src/css/hide_price.css',
        ],
    },
    'installable': True,
    'application': False,
}

