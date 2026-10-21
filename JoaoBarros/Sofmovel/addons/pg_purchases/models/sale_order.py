from odoo import api, fields, models
from collections import defaultdict
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    procurement_group_id = fields.Many2one('procurement.group', string="Grupo de Aprovisionamento")
    purchase_created = fields.Boolean(default=False)

    purchase_order_ids = fields.Many2many(
        'purchase.order',
        compute='_compute_purchase_order_ids',
        string='Ordens de Compra',
    )

    purchase_order_count = fields.Integer(
        string="Número de Ordens de Compra",
        compute='_compute_purchase_order_ids',
    )

    internal_transfer_ids = fields.One2many(
        comodel_name='stock.picking',
        compute='_compute_internal_transfer_ids',
        store=False,
        string='Transferências Internas'
    )

    @api.depends('name')
    def _compute_internal_transfer_ids(self):
        for order in self:
            order.internal_transfer_ids = self.env['stock.picking'].search([
                ('origin', '=', order.name),
                ('picking_type_id.code', '=', 'internal')
            ])

    @api.depends('procurement_group_id')
    def _compute_purchase_order_ids(self):
        for order in self:
            if order.procurement_group_id:
                pos = self.env['purchase.order'].search([
                    ('group_id', '=', order.procurement_group_id.id)
                ])
                order.purchase_order_ids = pos
                order.purchase_order_count = len(pos)
                _logger.info(f"[PG_PURCHASES] Recomputed {len(pos)} Purchase Orders for SO {order.name}")
            else:
                order.purchase_order_ids = self.env['purchase.order']
                order.purchase_order_count = 0

    def action_open_purchase_orders(self):
        self.ensure_one()
        if not self.procurement_group_id:
            raise UserError("Esta encomenda não possui compras geradas.")
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'domain': [('group_id', '=', self.procurement_group_id.id)],
            'name': 'Ordens de Compra',
            'target': 'current',
        }

    def open_generate_purchase_po_wizard(self):
        self.ensure_one()
        if self.state != 'sale':
            raise UserError("Só pode gerar ordens de compra para encomendas confirmadas.")

        if self.purchase_created:
            _logger.info(f"[PG_PURCHASES] Wizard opened: SO {self.name} already created POs")
            return {
                'type': 'ir.actions.act_window',
                'name': 'Confirmar Criação de Compras',
                'res_model': 'generate.purchase.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_sale_order_id': self.id},
            }
        else:
            return self.action_generate_purchase_orders()

    def action_generate_purchase_orders(self):
        self.ensure_one()
        _logger.info(f"[PG_PURCHASES] Starting PO generation for SO: {self.name} | Group: {self.procurement_group_id}")

        purchase_orders = []
        grouped_lines = defaultdict(list)

        for line in self.order_line:
            if line.display_type or not line.product_id.purchase_ok:
                continue
            if line.product_id.seller_ids:
                vendor = line.product_id.seller_ids[0].partner_id
                grouped_lines[vendor].append(line)
            else:
                raise UserError(f"Nenhum fornecedor definido para o produto '{line.product_id.display_name}'.")

        for vendor, lines in grouped_lines.items():
            _logger.info(f"[PG_PURCHASES] Creating PO for vendor {vendor.display_name} with group_id {self.procurement_group_id.id}")
            po_vals = {
                'partner_id': vendor.id,
                'origin': self.name,
                'origin_sale_order_id': self.id,
                'group_id': self.procurement_group_id.id,
                'order_line': [],
            }
            po_lines = []
            for line in lines:
                _logger.info(f"[PG_PURCHASES]   → Adding product - {line.product_id.display_name} x {line.product_uom_qty}")
                po_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'product_qty': line.product_uom_qty,
                    'product_uom': line.product_uom.id,
                    'price_unit': line.product_id.standard_price,
                    'date_planned': fields.Date.today(),
                }))
            po_vals['order_line'] = po_lines
            purchase_order = self.env['purchase.order'].create(po_vals)
            _logger.info(f"[PG_PURCHASES] PO {purchase_order.name} created")
            purchase_orders.append(purchase_order.id)

        self.purchase_created = True
        self._compute_purchase_order_ids()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Ordens de Compra',
            'res_model': 'purchase.order',
            'domain': [('id', 'in', purchase_orders)],
            'view_mode': 'tree,form',
        }


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    origin_sale_order_id = fields.Many2one('sale.order', string="Encomenda de Venda")
    
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_variant_desc = fields.Char(compute='_compute_variant_desc')

    def _compute_variant_desc(self):
        for line in self:
            line.product_variant_desc = ''

