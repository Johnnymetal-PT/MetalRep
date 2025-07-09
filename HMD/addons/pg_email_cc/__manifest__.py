# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.
{
    "name": "pg_email_cc",
    "version": "2.0",
    "author": "Techultra Solutions Private Limited",
    'company': 'TechUltra Solutions Private Limited',
    'website': "https://www.techultrasolutions.com/",
    "category": "Email",
    "summary": "Email Cc composer provided field  in mail composer wizard to set Cc mail address. Now no need to send multiple copy of email directly to the user, sender can be able to set multiple emails in 'Email Cc' with commma seperator.",
    "description": """
        Email Cc
        Mail Composer
        Email Composer
        Email Carbon Copy
        Carbon Copy
        Email
    """,
    "depends": ["mail","account"],
    "data": [
        "views/email_cc.xml",
    ],
    "images": [
        "static/description/main_screen.gif",
    ],
    "currency": "USD",
    "price": 10,
    "installable": True,
    "application": True,
    "license": "OPL-1",
}
