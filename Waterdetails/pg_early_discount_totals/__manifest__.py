{
    "name": "PG - Desconto de pronto pagamento nos totais",
    "summary": "Permite excluir linhas do desconto de pronto pagamento nas "
               "faturas (cliente e fornecedor) e mostra o total líquido e o valor em "
               "dívida já com o desconto deduzido, também na reconciliação bancária. "
               "Impede confirmar faturas e notas de crédito de cliente sem NIF "
               "(exceto Consumidor Final).",
    "version": "19.0.1.5.0",
    "category": "Accounting/Accounting",
    "author": "Parametro Global",
    "website": "https://parametro.global",
    "license": "LGPL-3",
    "depends": [
        "account",
        "account_accountant",
        "ptplus_partner",
    ],
    "data": [
        "views/account_move_views.xml",
        "views/bank_rec_widget_views.xml",
        "views/report_invoice.xml",
    ],
    "installable": True,
}
