{
    "name": "PG Prestashop Connector - Clients",
    "version": "17.0.1.0.0",
    "summary": "Sync Prestashop customers into Odoo contacts",
    "category": "Sales",
    "author": "PG",
    "depends": ["contacts"],
    "data": [
        "security/ir.model.access.csv",
        "views/prestashop_instance_views.xml",
    ],
    "installable": True,
    "application": False,
}
