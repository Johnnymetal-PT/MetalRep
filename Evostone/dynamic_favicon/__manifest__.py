{
    'name': 'Dynamic Favicon',
    'version': '18.0.1.0.0',
    'category': 'Website',
    'summary': 'Set favicon dynamically based on company logo',
    'description': """
        This module automatically sets the favicon based on the current company's logo.
        If no company logo is available, it falls back to the default Odoo favicon.
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['web', 'base'],
    'data': [
        'views/webclient_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dynamic_favicon/static/src/js/favicon_manager.js',
            'dynamic_favicon/static/src/xml/favicon_manager.xml',
        ],
        'web.assets_frontend': [
            'dynamic_favicon/static/src/js/favicon_manager.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}