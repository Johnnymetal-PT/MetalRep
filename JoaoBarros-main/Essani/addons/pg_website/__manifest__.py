{
    'name': 'PG Website',
    'version': '1.0',
    'category': 'Website',
    'summary': 'Alterar class container no website.mainpage',
    'description': """
        Este módulo altera class container no website.mainpage
    """,
    'author': 'Parâmetro Global, SA',
    'website': 'http://www.parametro.pt',
    'depends': ['base', 'product','website', 'website_sale'],
    'data': [
        'views/templates.xml',
        'views/website_menu.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'pg_website/static/src/css/custom_homepage.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
