from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class StockMove(models.Model):
    _inherit = 'stock.move'

    product_id = fields.Many2one('product.product', 'Product', required=True)
    partner_id = fields.Many2one(
        'res.partner',
        string='Endereço de destino',
        domain="[('type', 'in', ['contact', 'company'])]",
        compute='_compute_partner_id',
        store=True,
    )

    @api.depends('product_id')
    def _compute_partner_id(self):
        for move in self:
            if move.state == 'done' or not move.product_id:
                _logger.info(f"[COMPUTE PARTNER] Skipping computation for move {move.id} - state: {move.state}, product: {move.product_id}")
                move.partner_id = False
                continue

            company_id = move.company_id or self.env.user.company_id
            supplier_info = self.env['product.supplierinfo'].search([
                ('product_tmpl_id', '=', move.product_id.product_tmpl_id.id),
                ('company_id', 'in', [False, company_id.id])
            ], limit=1)
            
            if supplier_info:
                _logger.info(f"[COMPUTE PARTNER] Found supplier {supplier_info.partner_id.id} for product {move.product_id.id}")
                move.partner_id = supplier_info.partner_id
            else:
                _logger.info(f"[COMPUTE PARTNER] No supplier found for product {move.product_id.id}")
                move.partner_id = False

    def write(self, vals):
        # Detect changes to the partner_id field
        partner_changed = 'partner_id' in vals and any(
            move.partner_id != vals['partner_id'] for move in self
        )

        if partner_changed:
            _logger.info(f"[STOCK MOVE WRITE] Partner changed for stock moves {self.ids} - updating supplier info.")
            res = super(StockMove, self).write(vals)
            # Update supplier info for the affected stock moves
            self._update_supplier_info()
        else:
            _logger.info(f"[STOCK MOVE WRITE] No partner change detected for stock moves {self.ids}.")
            res = super(StockMove, self).write(vals)

        return res

    def _update_supplier_info(self):
        """Automatically update supplier info for the product based on the current partner_id."""
        for move in self:
            if not move.partner_id or not move.product_id:
                _logger.info(f"[UPDATE SUPPLIER INFO] Skipping update for move {move.id} - missing partner or product")
                continue

            supplier_info = self.env['product.supplierinfo'].search([
                ('product_tmpl_id', '=', move.product_id.product_tmpl_id.id),
                ('company_id', '=', move.company_id.id)
            ], limit=1)

            if supplier_info:
                _logger.info(f"[UPDATE SUPPLIER INFO] Updating supplier info {supplier_info.id} for product {move.product_id.id} with new partner {move.partner_id.id}")
                supplier_info.write({'partner_id': move.partner_id.id})
            else:
                _logger.info(f"[UPDATE SUPPLIER INFO] Creating new supplier info for product {move.product_id.id} with partner {move.partner_id.id}")
                self.env['product.supplierinfo'].create({
                    'product_tmpl_id': move.product_id.product_tmpl_id.id,
                    'partner_id': move.partner_id.id,
                    'min_qty': 0.00,
                    'price': 0.00,
                    'currency_id': self.env.user.company_id.currency_id.id,
                    'delay': 7,
                })
