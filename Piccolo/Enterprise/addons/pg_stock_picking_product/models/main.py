import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)  # Initialize logger

class StockPicking(models.Model):
    _inherit = "stock.picking"

    manufactured_product_id = fields.Many2one(
        "product.product",
        string="Produto da Produção",
        compute="_compute_manufactured_product",
        store=True,
    )

    manufacturing_origin = fields.Char(
        string="Ordem de Venda",
        compute="_compute_manufacturing_origin",
        store=True,
    )

    @api.depends("group_id")
    def _compute_manufactured_product(self):
        for picking in self:
            _logger.info(f"🔎 Checking Stock Picking ID: {picking.id}")

            if not picking.group_id:
                _logger.warning(f"⚠ No Group ID found for Stock Picking {picking.id}")
                picking.manufactured_product_id = False
                continue

            _logger.info(f"🔗 Group ID: {picking.group_id.name}")

            # Search for the corresponding Manufacturing Order
            mo = self.env["mrp.production"].search([("procurement_group_id", "=", picking.group_id.id)], limit=1)

            if mo:
                _logger.info(f"✅ Found MO {mo.id} for Picking {picking.id} with Product {mo.product_id.id} - {mo.product_id.name}")
                picking.manufactured_product_id = mo.product_id
            else:
                _logger.warning(f"⚠ No Manufacturing Order found for Group ID {picking.group_id.id}")
                picking.manufactured_product_id = False

    @api.depends("group_id")
    def _compute_manufacturing_origin(self):
        for picking in self:
            _logger.info(f"🔎 Checking Manufacturing Order for Picking ID: {picking.id}")

            if not picking.group_id:
                _logger.warning(f"⚠ No Group ID found for Stock Picking {picking.id}")
                picking.manufacturing_origin = False
                continue

            # Search for the corresponding Manufacturing Order
            mo = self.env["mrp.production"].search([("procurement_group_id", "=", picking.group_id.id)], limit=1)

            if mo:
                _logger.info(f"✅ Found MO {mo.id} for Picking {picking.id} with Origin {mo.origin}")
                picking.manufacturing_origin = mo.origin
            else:
                _logger.warning(f"⚠ No Manufacturing Order found for Group ID {picking.group_id.id}")
                picking.manufacturing_origin = False

