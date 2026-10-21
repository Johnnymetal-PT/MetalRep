# Copyright 2025 MH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'MH Return Credit Note',
    'version': '18.0.2.0.0',
    'category': 'Inventory/Stock',
    'summary': 'Criar nota de crédito automaticamente ao devolver picking (vendas e compras)',
    'description': """
MH Return Credit Note
=====================

Este módulo permite criar notas de crédito automaticamente quando
se processa uma devolução de mercadoria.

Funcionalidades:
- Opção no wizard de devolução para criar nota de crédito
- Suporte a devoluções de VENDAS (nota de crédito cliente - out_refund)
- Suporte a devoluções de COMPRAS (nota de crédito fornecedor - in_refund)
- Nota de crédito criada com as quantidades devolvidas
- Link bidirecional entre picking e nota de crédito
- Smart button no picking para aceder à nota de crédito

Fluxo Vendas:
1. Ir ao picking de entrega validado
2. Clicar "Devolver"
3. Marcar "Criar Nota de Crédito"
4. Confirmar devolução
5. Picking de devolução + Nota de crédito cliente criados automaticamente

Fluxo Compras:
1. Ir ao picking de recepção validado
2. Clicar "Devolver"
3. Marcar "Criar Nota de Crédito"
4. Confirmar devolução
5. Picking de devolução + Nota de crédito fornecedor criados automaticamente
    """,
    'author': 'MH',
    'website': 'https://www.mh.co.mz',
    'license': 'AGPL-3',
    'depends': [
        'stock',
        'sale_stock',
        'purchase_stock',
        'account',
        'mh_sale',  # Para lot_id em account.move.line
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/stock_return_picking_views.xml',
        'views/stock_picking_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
