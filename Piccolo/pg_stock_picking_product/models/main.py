"""Cruza Stock Picking com a Manufacturing Order via procurement group.

Acrescenta no picking dois campos auxiliares stored:
- ``manufactured_product_id``: produto final da MO ligada;
- ``manufacturing_origin``: origin da MO (tipicamente o nome da SO).

Ambos calculados a partir de ``stock.picking.group_id``.
"""
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


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
            _logger.info("Checking Stock Picking ID: %s", picking.id)

            if not picking.group_id:
                # Sem procurement group nao ha como encontrar a MO.
                picking.manufactured_product_id = False
                continue

            # Procurement group e a chave de juncao entre o picking
            # de consumo e a MO que o originou.
            mo = self.env["mrp.production"].search(
                [("procurement_group_id", "=", picking.group_id.id)],
                limit=1,
            )

            if mo:
                picking.manufactured_product_id = mo.product_id
            else:
                picking.manufactured_product_id = False

    @api.depends("group_id")
    def _compute_manufacturing_origin(self):
        for picking in self:
            if not picking.group_id:
                picking.manufacturing_origin = False
                continue

            # Mesma lookup do computed acima - mantida em separado para
            # que cada campo possa ser recomputed independentemente pelo ORM.
            mo = self.env["mrp.production"].search(
                [("procurement_group_id", "=", picking.group_id.id)],
                limit=1,
            )

            if mo:
                picking.manufacturing_origin = mo.origin
            else:
                picking.manufacturing_origin = False
