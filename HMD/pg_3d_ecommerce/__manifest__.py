{
    "name": "eCommerce: Product model viewer",
    "summary": "3D model viewer for e-commerce products",
    "version": "18.0.2.0.0",
    "development_status": "Beta",
    "category": "Website",
    "website": "https://github.com/OCA/e-commerce",
    "author": "TAKOBI, Openindustry.it, Odoo Community Association (OCA)",
    "maintainers": ["eLBati"],
    "license": "AGPL-3",
    "depends": [
        "pg_3d_viewer",
        "website_sale",
    ],
    "data": [
        "views/frontend_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "pg_3d_ecommerce/static/src/js/product_model_viewer.js",
            "pg_3d_ecommerce/static/src/scss/product_model_viewer.scss",
        ],
    },
    "application": False,
    "installable": True,
}
