"""Campo agregado com a descricao das linhas para listas/filtros.

``order_line_description`` concatena os ``name`` de todas as
``sale.order.line`` num unico Char e implementa ``search`` para
permitir filtrar SOs por texto presente nas linhas.
"""
from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # store=False: nao guarda em BD. O custo recai no compute on demand;
    # o search method abaixo trata da pesquisa via subquery.
    order_line_description = fields.Char(
        string="Descrição do Produto",
        compute="_compute_order_line_description",
        store=False,
        search="_search_order_line_description",
    )

    def _compute_order_line_description(self):
        """Concatena as descricoes das linhas para visualizacao."""
        for order in self:
            order.order_line_description = ", ".join(order.order_line.mapped("name"))

    def _search_order_line_description(self, operator, value):
        """Permite filtrar SOs por texto presente em qualquer linha.

        Resolve por subquery as ``sale.order.line`` cujo ``name``
        bate com o valor pesquisado e devolve um dominio com os
        ``order_id`` correspondentes.
        """
        orders = self.env['sale.order.line'].search(
            [('name', 'ilike', value)],
        ).mapped('order_id')
        return [('id', 'in', orders.ids)]
