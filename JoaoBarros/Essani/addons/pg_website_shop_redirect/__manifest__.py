# __manifest__.py
{
    'name': 'PG Website Shop Redirect',
    'version': '1.0',
    'category': 'Website',
    'summary': 'Redirect users from /shop if not logged in',
    'author': 'Your Name or Company',
    'depends': ['website_sale'],
    'data': [
        'views/templates.xml',
    ],
    'installable': True,
    'application': False,
}
