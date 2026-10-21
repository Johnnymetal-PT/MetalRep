{
    'name': 'MH Import Document Adjustments',
    'version': '18.0.1.1.0',
    'category': 'Inventory/Purchase',
    'summary': 'Ajustes pós-factura para Documentos de Importação',
    'description': """
        Permite criar documentos de Ajuste (ADJ) ligados a um Documento de
        Importação (IMP) finalizado, sem modificar o IMP original.

        Cenário típico: factura do fornecedor traz valores acima da PO
        (ex.: linha "Acerto Compras Custo" sem PO). Esses valores são
        detectados ao postar a factura, geram um documento ADJ em rascunho.
        O operador revê, distribui e aplica — cria 2º landed cost + ajuste CMV
        para quantidades já vendidas, usando a conta de output de stock de
        cada produto.
    """,
    'author': 'MH',
    'depends': [
        'mh_purchase',
        'stock_landed_costs',
        'stock_account',
        'account',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/mail_activity_data.xml',
        'data/product_data.xml',
        'views/import_document_adjustment_views.xml',
        'views/import_document_inherit_views.xml',
        'views/account_move_inherit_views.xml',
        'views/res_config_settings_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
