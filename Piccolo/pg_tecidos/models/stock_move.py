"""Fornecedor no stock.move alinhado com o product.supplierinfo.

Acrescenta ``partner_id`` (Fornecedor) ao move, computed do primeiro
``product.supplierinfo`` do template do produto. Quando o utilizador
muda manualmente o fornecedor no move, refletimos a alteracao no
supplierinfo do template (cria ou atualiza).
"""
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    product_id = fields.Many2one('product.product', 'Product', required=True)
    partner_id = fields.Many2one(
        'res.partner',
        string='Fornecedor',
        domain="[('type', 'in', ['contact', 'company'])]",
        compute='_compute_partner_id',
        store=True,
        readonly=False,
    )

    @api.depends('product_id')
    def _compute_partner_id(self):
        for move in self:
            # Nao mexer em moves ja realizados (historico).
            if move.state == 'done' or not move.product_id:
                move.partner_id = False
                continue

            company_id = move.company_id or self.env.user.company_id
            # company_id=False no supplierinfo significa "todas as companies".
            supplier_info = self.env['product.supplierinfo'].search([
                ('product_tmpl_id', '=', move.product_id.product_tmpl_id.id),
                ('company_id', 'in', [False, company_id.id]),
            ], limit=1)

            move.partner_id = supplier_info.partner_id if supplier_info else False

    def write(self, vals):
        # Detetar mudanca de partner_id ANTES de chamar super para
        # ter o valor antigo disponivel no diff.
        partner_changed = 'partner_id' in vals and any(
            move.partner_id != vals['partner_id'] for move in self
        )

        if partner_changed:
            res = super(StockMove, self).write(vals)
            # Replicar a mudanca no supplierinfo do template, para
            # que o procurement seguinte saiba a quem comprar.
            self._update_supplier_info()
        else:
            res = super(StockMove, self).write(vals)

        return res

    def _update_supplier_info(self):
        """Sincroniza partner_id do move com o supplierinfo do template."""
        for move in self:
            if not move.partner_id or not move.product_id:
                continue

            supplier_info = self.env['product.supplierinfo'].search([
                ('product_tmpl_id', '=', move.product_id.product_tmpl_id.id),
                ('company_id', '=', move.company_id.id),
            ], limit=1)

            if supplier_info:
                supplier_info.write({'partner_id': move.partner_id.id})
            else:
                self.env['product.supplierinfo'].create({
                    'product_tmpl_id': move.product_id.product_tmpl_id.id,
                    'partner_id': move.partner_id.id,
                    'min_qty': 0.00,
                    'price': 0.00,
                    'currency_id': self.env.user.company_id.currency_id.id,
                    'delay': 7,
                })
