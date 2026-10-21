# -*- coding: utf-8 -*-
from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # O nativo depende só de 'move_id'; acrescentamos o flag e a posição fiscal
    # para recalcular a conta quando a NC muda de estado/mercado.
    @api.depends('move_id', 'move_id.mh_purchase_return', 'move_id.fiscal_position_id')
    def _compute_account_id(self):
        super()._compute_account_id()
        for line in self.filtered(
                lambda l: l.display_type == 'product' and l.product_id
                and l.move_id.move_type == 'in_refund'
                and l.move_id.mh_purchase_return):
            accounts = line.with_company(line.company_id) \
                .product_id.product_tmpl_id._get_product_accounts()
            ret = accounts.get('stock_return')
            if not ret:
                continue
            # Aplica o mapa da posição fiscal (mercado/regime), como o
            # mh_market_stock faz no lado do stock — a conta 'stock_return' é
            # custom e não é remapeada pelo get_product_accounts nativo.
            fp = line.move_id.fiscal_position_id
            if fp:
                ret = fp.map_account(ret) or ret
            line.account_id = ret
