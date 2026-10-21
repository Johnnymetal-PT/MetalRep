{
    "name": "PG Purchases from Sales Order",
    "version": "17.0.1.0.1",
    "depends": ["sale", "purchase"],
    "author": "Parâmetro Global",
    "category": "Sales",
    "summary": "Gerar Compras a partir de Encomendas de Venda",
    "data": [
        "views/sale_order_view.xml",
        "views/actions.xml",
        "views/generate_purchase_wizard_view.xml",
        "security/ir.model.access.csv"
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
