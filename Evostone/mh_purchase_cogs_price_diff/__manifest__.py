# -*- coding: utf-8 -*-
{
    'name': 'MH Purchase COGS Price Difference',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Inventory',
    'summary': 'Encaminha a diferença de preço da parte VENDIDA das facturas de '
               'fornecedor para o CMV, em vez de se anular na conta de trânsito.',
    'description': """
Correcção da diferença de preço (COGS) em facturas de fornecedor
=================================================================

No esquema anglo-saxónico do Odoo, quando uma factura de fornecedor tem preço
diferente do custo de recepção e parte da mercadoria já foi VENDIDA, o Odoo cria
linhas `cogs` para reconhecer a diferença de custo da venda.

Quando a **conta de despesa (expense)** da categoria é a MESMA que a **conta de
stock input** (caso PCMP/AVCO em que a conta de trânsito limpa o input na linha da
factura), essas linhas `cogs` caem ambas na conta de input e **anulam-se** —
deixando o custo extra da venda preso na conta de trânsito, em vez de ir para o CMV.

Este módulo, ao postar a factura de fornecedor, detecta essa situação e lança a
correcção: **D CMV (stock output) / C conta de trânsito (stock input)** pela
parte vendida — alinhando o CMV e fechando a conta de trânsito, **sem mexer na
conta de valorização nem no value_svl**, que já estão correctos.
""",
    'author': 'MHC',
    'depends': ['purchase_stock', 'stock_account', 'account'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
