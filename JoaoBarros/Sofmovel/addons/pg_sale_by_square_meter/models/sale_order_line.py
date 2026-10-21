import logging
from odoo import models, fields, api
from odoo.tools.float_utils import float_compare

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

    def _uses_square_meter_qty(self):
        self.ensure_one()
        return bool(
            self.comprimento > 0
            and self.largura > 0
            and self.area > 0
        )

    def _get_square_meter_qty(self):
        self.ensure_one()
        if self.comprimento > 0 and self.largura > 0:
            return self.comprimento * self.largura
        return 0.0

    def _sync_product_qty_from_dimensions(self):
        for line in self:
            if not line._uses_square_meter_qty():
                continue
            target_qty = line._get_square_meter_qty()
            if target_qty <= 0:
                continue
            rounding = line.product_uom.rounding or 0.01
            if float_compare(line.product_uom_qty, target_qty, precision_rounding=rounding) != 0:
                line.with_context(skip_square_meter_qty_sync=True).product_uom_qty = target_qty

    @api.onchange('product_id', 'product_uom', 'comprimento', 'largura')
    def _onchange_square_meter_dimensions(self):
        self._sync_product_qty_from_dimensions()

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._sync_product_qty_from_dimensions()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get('skip_square_meter_qty_sync') and {'product_id', 'product_uom', 'comprimento', 'largura'} & set(vals):
            self._sync_product_qty_from_dimensions()
        return res

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
            qty = line.product_uom_qty
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
        """Keep tax lines aligned with the synced sale quantity."""
        res = super()._convert_to_tax_base_line_dict()
        res['quantity'] = self.product_uom_qty
        return res
