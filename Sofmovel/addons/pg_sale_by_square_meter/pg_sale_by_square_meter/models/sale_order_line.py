import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    comprimento = fields.Float(string='Comprimento (m)')
    largura = fields.Float(string='Largura (m)')
    area = fields.Float(string='\u00c1rea (m\u00b2)', compute='_compute_area', store=True)

    @api.depends('comprimento', 'largura')
    def _compute_area(self):
        for line in self:
            if line.comprimento > 0 and line.largura > 0:
                line.area = line.comprimento * line.largura
            else:
                line.area = 0.0

    @api.depends(
        'product_uom_qty',
        'discount',
        'price_unit',
        'tax_id',
        'currency_id',
        'company_id',
        'order_id.partner_shipping_id',
        'order_id.currency_id',
        'comprimento',
        'largura',
    )
    def _compute_amount(self):
        for line in self:
            qty = line.product_uom_qty * (line.area if line.area > 0 else 1)
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(
                price,
                line.order_id.currency_id,
                qty,
                product=line.product_id,
                partner=line.order_id.partner_shipping_id,
            )
            line.update(
                {
                    'price_subtotal': taxes['total_excluded'],
                    'price_total': taxes['total_included'],
                    'price_tax': taxes['total_included'] - taxes['total_excluded'],
                }
            )
            _logger.info(
                "Computed line %s qty=%s area=%s subtotal=%s total=%s",
                line.id,
                qty,
                line.area,
                taxes['total_excluded'],
                taxes['total_included'],
            )
        orders = self.mapped('order_id')
        if orders:
            orders._compute_tax_totals()
            for order in orders:
                _logger.info(
                    "Updated tax totals for order %s: %s",
                    order.id,
                    order.tax_totals,
                )

    def _convert_to_tax_base_line_dict(self):
        """Extend to use the area adjusted quantity when preparing tax lines."""
        res = super()._convert_to_tax_base_line_dict()
        qty = self.product_uom_qty * (self.area if self.area > 0 else 1)
        res['quantity'] = qty
        return res
