{
    'name': 'PG Shop Filters',
    'version': '1.0',
    'summary': 'Add accordion functionality to the product attributes on the website.',
    'category': 'Website',
    'author': 'Tone Biclas',
    'depends': ['website', 'website_sale', 'web'],
    'data': [
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'pg_shop_filters/static/src/js/accordion.js',
            'pg_shop_filters/static/src/css/styles.css',
        ],
    },
    'installable': True,
    'application': False,
}
