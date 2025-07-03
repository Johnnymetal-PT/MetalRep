# -*- coding: utf-8 -*-

{
    'name': 'PG Website Scroll Back To Top',
    'summary': 'This Module Will Add Back To Top Button On Website For All Pages Like Shop,Blog,Events etc.',
    'description': """
        This This Module Will Add Back To Top Button On Website For All Pages Like Shop,Blog,Events etc.
    """,
    'category': 'Website',
    'version': '17.0.1.0',
    'author': "Bytesfuel",
    'website': "https://bytesfuel.com/",
    'license': 'LGPL-3',
    "sequence":  1,
    'data': [
        'views/back_to_top.xml',
    ],

    'assets': {
        'web.assets_frontend': [
            '/pg_website_scroll_top_bytesfuel/static/src/js/back_to_top.js',
            '/pg_website_scroll_top_bytesfuel/static/src/scss/back_to_top.scss',
        ],
    },
    'images': ['static/description/banner.png'],
    'depends': ['website'],
    'installable': True,
    'application': True,
}
