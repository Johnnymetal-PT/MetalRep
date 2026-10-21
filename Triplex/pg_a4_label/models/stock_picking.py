# -*- coding: utf-8 -*-
"""Relatório e ação de impressão de etiquetas A4 a partir de transferências de stock.

Ver o __manifest__.py para o objetivo. Resumo: um relatório QWeb que recebe os pickings
e um método no stock.picking que dispara a impressão.
"""
from odoo import models
import logging
_logger = logging.getLogger(__name__)

class ReportStockPickingLabel(models.AbstractModel):
    # O nome técnico tem de ser "report.<nome_do_template_qweb>" para o Odoo ligar o
    # modelo ao template; aqui o template é report_simple_label4x7.
    _name = 'report.product.report_simple_label4x7'
    _description = 'Stock Picking Labels Report'

    def _get_report_values(self, docids, data=None):
        # Disponibiliza os pickings ao template QWeb sob a chave `docs`.
        docs = self.env['stock.picking'].browse(docids)
        _logger.info("Docs passed to report: %s", docs)
        return {
            'docs': docs,
        }

class StockPicking(models.Model):
    _inherit = "stock.picking"

    def print_labels(self):
        """Dispara a ação de relatório das etiquetas para os pickings selecionados."""
        report = self.env.ref('pg_a4_label.action_report_stock_picking_labels')
        return report.report_action(self)  # `self` (os pickings) é passado como `docs`

