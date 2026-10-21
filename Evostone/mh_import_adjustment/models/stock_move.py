# -*- coding: utf-8 -*-
import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    adjusted_unit_cost = fields.Float(
        string='Custo Unitário Ajustado (ADJ)',
        digits='Product Price',
        copy=False,
        readonly=True,
        help='Custo unitário efectivo após aplicação de ADJ (Ajuste de Importação). '
             'Inclui o unit_cost original + ajuste de Landed Cost rateado pela '
             'qty vendida. Usado para que devoluções a partir deste OUT '
             'entrem ao custo real (e não ao unit_cost histórico), evitando '
             'orfãos contabilísticos em CMV.',
    )

    def _get_price_unit(self):
        """Override (path Odoo standard): para devoluções de OUT com ADJ
        aplicado, usar `adjusted_unit_cost`. Em produtos PCMP, o Stone
        intercepta via `_get_pcmp_in_svl_vals` — o override abaixo
        também o cobre.
        """
        if (
            self.origin_returned_move_id
            and self.origin_returned_move_id.adjusted_unit_cost
            and self.product_id.cost_method == 'pcmp'
        ):
            adjusted = self.origin_returned_move_id.adjusted_unit_cost
            if self.lot_ids:
                return {lot: adjusted for lot in self.lot_ids}
            return {self.env['stock.lot']: adjusted}
        return super()._get_price_unit()

    def _get_pcmp_in_svl_vals(self, forced_quantity):
        """Override (path Stone PCMP): força custo do ADJ em devoluções
        quando o OUT original tem `adjusted_unit_cost` populado.

        O método Stone original usa `abs(total_value/total_qty)` das SVLs
        do OUT original — que é o custo histórico (sem ADJs aplicados
        depois). Aqui interceptamos antes de chamar super() para passar
        o `adjusted_unit_cost` via `price_unit` temporário.
        """
        if (
            self.product_id.cost_method == 'pcmp'
            and self.origin_returned_move_id
            and self.origin_returned_move_id.adjusted_unit_cost
        ):
            adjusted = self.origin_returned_move_id.adjusted_unit_cost
            _logger.info(
                "Devolução com ADJ: move %s usa adjusted_unit_cost=%s "
                "(em vez de SVL.unit_cost original)",
                self.id, adjusted,
            )
            # Construir o resultado seguindo a estrutura do método original.
            # Reutilizamos a parte da agregação e quantidade do super, mas
            # substituímos unit_cost no fim.
            vals_list = super()._get_pcmp_in_svl_vals(forced_quantity)
            for vals in vals_list:
                qty = vals.get('quantity', 0.0)
                vals['unit_cost'] = adjusted
                vals['value'] = adjusted * qty
            return vals_list
        return super()._get_pcmp_in_svl_vals(forced_quantity)
