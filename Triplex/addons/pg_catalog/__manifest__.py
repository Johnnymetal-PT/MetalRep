{
    'name': 'PG Product Catalog',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Print a detailed product catalog',
    'author': 'Your Name',
    'depends': ['product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_view.xml',
        'report/product_template_pdf.xml',
        'report/product_template_pdf_255.xml',
        'report/product_template_pdf_usa.xml',
        'report/product_template_pages.xml',
        'report/product_template_pages_255.xml',
        'report/product_template_pages_usa.xml',
        'report/product_template_pdf_maisondoree.xml',
        'report/product_template_pages_maisondoree.xml',
        'report/product_template_report_action.xml'
    ],
    'installable': True,
    'application': False,
}

