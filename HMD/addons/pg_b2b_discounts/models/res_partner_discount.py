from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_total_spendings = fields.Float(string="Total Spendings", compute="_compute_total_spendings", store=True)
    x_discount_tier = fields.Selection([
        ('none', 'None'),
        ('bronze', 'Bronze - 10%'),
        ('silver', 'Silver - 15%'),
        ('gold', 'Gold - 20%'),
        ('diamond', 'Diamond - 25%'),
    ], string="Discount Tier", default='none')
    x_studio_fidelizado = fields.Boolean(string="Fidelized")

    sale_orders = fields.One2many('sale.order', 'partner_id', string="Sales Orders")

    @api.depends('sale_orders', 'sale_orders.state', 'sale_orders.amount_total', 'x_studio_fidelizado')
    def _compute_total_spendings(self):
        for partner in self:
            _logger.info(f"Processing partner: {partner.name} (ID: {partner.id})")

            if not partner.x_studio_fidelizado:
                _logger.info(f"Resetting partner {partner.name} (not fidelized).")
                partner.x_total_spendings = 0.0
                partner.x_discount_tier = 'none'
                default_pricelist = self._get_default_pricelist(partner.company_id.id)
                partner.property_product_pricelist = default_pricelist
                continue

            sales_orders = partner.sale_orders.filtered(lambda so: so.state in ['sale', 'done'])
            total_spent = sum(sales_orders.mapped('amount_total'))
            partner.x_total_spendings = total_spent

            previous_tier = partner.x_discount_tier
            if total_spent >= 15000:
                partner.x_discount_tier = 'diamond'
            elif total_spent >= 5000:
                partner.x_discount_tier = 'gold'
            elif total_spent >= 1500:
                partner.x_discount_tier = 'silver'
            elif total_spent > 0:
                partner.x_discount_tier = 'bronze'
            else:
                partner.x_discount_tier = 'none'

            if partner.x_discount_tier != previous_tier:
                self._assign_combined_pricelist(partner)

    def _get_default_pricelist(self, company_id):
        prop = self.env['ir.property'].search([
            ('name', '=', 'property_product_pricelist'),
            ('res_id', '=', False),
            ('company_id', '=', company_id)
        ], limit=1)
        if prop:
            return self.env['product.pricelist'].browse(int(prop.value_reference.split(',')[1]))
        return self.env['product.pricelist'].search([], limit=1)

    def _assign_combined_pricelist(self, partner):
        if not partner.x_studio_fidelizado:
            return

        descontos = self.env['product.pricelist'].search([('name', '=', 'Descontos')], limit=1)
        tier_name = {
            'bronze': 'Bronze Tier',
            'silver': 'Silver Tier',
            'gold': 'Gold Tier',
            'diamond': 'Diamond Tier',
        }.get(partner.x_discount_tier)
        tier = self.env['product.pricelist'].search([('name', '=', tier_name)], limit=1)

        if descontos and tier:
            combined = self._create_combined_pricelist(partner, descontos, tier)
            partner.property_product_pricelist = combined
        elif tier:
            partner.property_product_pricelist = tier

    def _create_combined_pricelist(self, partner, descontos, tier):
        name = f"Combined ({partner.name})"
        combined = self.env['product.pricelist'].search([('name', '=', name)], limit=1)

        if not combined:
            combined = self.env['product.pricelist'].create({
                'name': name,
                'currency_id': descontos.currency_id.id,
            })

        combined.item_ids.unlink()
        descontos.item_ids.copy(default={'pricelist_id': combined.id})
        tier.item_ids.copy(default={'pricelist_id': combined.id})
        return combined

    @api.onchange('x_discount_tier')
    def _onchange_discount_tier(self):
        if self.x_studio_fidelizado:
            self._assign_combined_pricelist(self)
        else:
            self.property_product_pricelist = self._get_default_pricelist(self.company_id.id)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders._apply_tier_discount_if_empty()
        return orders

    def _apply_tier_discount_if_empty(self):
        discount_map = {
            'bronze': 10.0,
            'silver': 15.0,
            'gold': 20.0,
            'diamond': 25.0,
        }

        for order in self:
            tier = order.partner_id.x_discount_tier
            discount = discount_map.get(tier, 0.0)
            _logger.info(f"[TIER DISCOUNT] Partner: {order.partner_id.name} | Tier: {tier} | Discount: {discount}%")

            for line in order.order_line:
                if line.discount == 0.0:
                    _logger.info(f"[TIER DISCOUNT] Applying to line '{line.name}': setting from 0.0 to {discount}")
                    line.discount = discount
                else:
                    _logger.info(f"[TIER DISCOUNT] Line '{line.name}' already has discount {line.discount}, skipping")
