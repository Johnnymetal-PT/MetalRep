{
    "name": "Purchase Line Refund To Invoice Qty",
    "summary": """Permite decidir se a quantidade de notas de crédito de fornecedor
                deve ser considerada como quantidade a re-faturar""",
    "version": "18.0.1.0.0",
    "category": "Purchase",
    "author": "MH, based on OCA sale_line_refund_to_invoice_qty",
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": ["purchase", "mh_purchase"],
    "data": [
        "views/account_move_views.xml",
        "views/purchase_order_views.xml",
        "wizards/account_move_reversal_view.xml",
    ],
    "pre_init_hook": "pre_init_hook",
}
