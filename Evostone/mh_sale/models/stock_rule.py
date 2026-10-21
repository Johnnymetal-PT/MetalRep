from odoo import models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_custom_move_fields(self):
        """Override para adicionar campos customizados de dimensões

        Este método retorna lista de campos que devem ser copiados
        do procurement 'values' para o stock.move automaticamente.

        Os campos length, width, thickness e units_qty são adicionados
        ao sale.order.line via _prepare_procurement_values() e aqui
        são transferidos para o stock.move.
        """
        fields = super()._get_custom_move_fields()
        fields += ['length', 'width', 'thickness', 'units_qty']
        return fields
