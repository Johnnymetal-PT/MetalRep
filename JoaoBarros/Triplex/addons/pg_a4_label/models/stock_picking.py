from odoo import models
import logging
_logger = logging.getLogger(__name__)

class ReportStockPickingLabel(models.AbstractModel):
    _name = 'report.product.report_simple_label4x7'
    _description = 'Stock Picking Labels Report'

    def _get_report_values(self, docids, data=None):
        docs = self.env['stock.picking'].browse(docids)
        _logger.info("Docs passed to report: %s", docs)
        return {
            'docs': docs,
        }

class StockPicking(models.Model):
    _inherit = "stock.picking"

    def print_labels(self):
        """
        Generate the stock picking label report with proper context.
        """
        report = self.env.ref('pg_a4_label.action_report_stock_picking_labels')
        return report.report_action(self)  # Pass `self` as `docs`

