{
    'name': 'PG Web Attachment PDF View',
    'version': '1.0',
    'category': 'Website',
    'summary': 'View product PDF attachments in a new tab on the website',
    'description': 'Allows users to view product PDF attachments in a new tab on the product webpage instead of downloading them.',
    'author': 'Parâmetro Global SA',
    'depends': ['website_sale','base','web','product'],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_attachment_access_rights.xml',
        'security/ir_attachment_rules.xml',
        'views/product_template_views.xml',
        'views/website_product_template.xml',
        'views/dynamic_snippet_filter.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'pg_attach_pdf_view/static/src/js/attachment_preview.js',
        ],
    },
    'installable': True,
    'application': False,
}
