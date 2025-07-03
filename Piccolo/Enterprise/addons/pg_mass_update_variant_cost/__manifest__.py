{
    "name": "PG Update Mass variants",

    'version': "17.0",

   
    'category': "Sale",

    "summary": " Update the cost price in multiple product variants with a single click.",
    'author': "INKERP",
    'website': "http://www.inkerp.com/",

    "depends": ["product"],

    "data": ["views/product_product_view.xml",
             "security/ir.model.access.csv",
             'wizard/mass_update_variant_cost_wizard.xml',],
    
    'images': ['static/description/banner.png'],
    'license': "OPL-1",
    'installable': True,
    'application': True,
    'auto_install': False,
}

