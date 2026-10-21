# -*- coding: utf-8 -*-
{
    'name': 'MH Mercado Nacional/Externo — Contas de Stock',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Accounting',
    'summary': 'Conta de entrada de stock segue a posição fiscal (Nacional vs Externo)',
    'description': """
        Contas de stock por mercado (Nacional vs Externo)
        ==================================================

        Problema:
        - A posição fiscal remapeia a conta de gasto/entrada da FACTURA, mas NÃO
          toca nas contas de VALORIZAÇÃO de stock (recepção), que vêm só da
          categoria. Resultado: num artigo comprado dos dois mercados, a factura
          cai na conta ME e a recepção fica na conta MN -> a conta-ponte de
          entrada nunca fecha a zero (des-sincroniza).

        Solução:
        - Alinha a conta de ENTRADA de stock com a posição fiscal da compra,
          aplicando o MESMO mapa de contas da posição fiscal (ex.: 21111 -> 21123).
        - A conta de VALORIZAÇÃO (o activo, ex.: 223) NÃO é remapeada: o bem é o
          mesmo venha de que mercado vier.
        - Um só artigo, uma só categoria, comprado dos dois mercados, com contas
          GL separadas por mercado e a conta de entrada a fechar a zero.

        Notas:
        - Fonte única de verdade: o mapa de contas da posição fiscal (o mesmo que
          a factura usa). Se o mapa estiver vazio, o módulo é inerte.
        - Cobre devoluções (herda a posição fiscal do movimento original) para
          evitar saldos pendurados de Input/Output.
        - Landed costs entram na conta de valorização (não remapeada) -> compatível.

        Automatismo da posição fiscal do parceiro (res.partner):
        - Ao criar/mudar o país de um parceiro (cliente ou fornecedor), carimba
          automaticamente a posição fiscal pelo país (auto-detecção nativa
          _get_fiscal_position), só se estiver vazia e houver país. Garante que a
          compra/venda apanha a posição fiscal certa para o remapeamento MN/ME.
    """,
    'author': 'MH',
    'website': '',
    'depends': ['stock_account', 'purchase_stock'],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
