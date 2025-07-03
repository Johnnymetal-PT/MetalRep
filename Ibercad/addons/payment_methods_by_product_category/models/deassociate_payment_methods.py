from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    restrict_payment_paypal = fields.Boolean(string="Restrict PayPal Payment", store=True, default=False)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    restrict_payment_paypal = fields.Boolean(
        string="Restrict PayPal Payment",
        compute="_compute_restrict_payment_paypal",
        store=True
    )

    @api.depends('order_line.product_id')
    def _compute_restrict_payment_paypal(self):
        for order in self:
            order.restrict_payment_paypal = any(
                line.product_id.product_tmpl_id.restrict_payment_paypal
                for line in order.order_line
            )

    # Override the method to pass the flag to the invoice
    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals['restrict_payment_paypal'] = self.restrict_payment_paypal
        return invoice_vals


class AccountMove(models.Model):
    _inherit = 'account.move'

    restrict_payment_paypal = fields.Boolean(
        string="Restrict PayPal Payment",
        store=True,
        readonly=True
    )

    @api.model
    def create(self, vals):
        # Set the restrict_payment_paypal flag from the sale order if it's not already set
        if not vals.get('restrict_payment_paypal') and vals.get('invoice_origin'):
            sale_order = self.env['sale.order'].search([('name', '=', vals['invoice_origin'])], limit=1)
            if sale_order:
                vals['restrict_payment_paypal'] = sale_order.restrict_payment_paypal
        return super(AccountMove, self).create(vals)
    


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    @api.onchange('line_ids')
    def _onchange_line_ids(self):
        restricted_providers = ['paypal', 'stripe', 'adyen']
        restrict_payment = False

        # Check if the invoice has restricted payment flag
        for move in self.line_ids.mapped('move_id'):
            if move.restrict_payment_paypal:
                restrict_payment = True
                break

        # If restriction is active, filter out the restricted payment methods
        if restrict_payment:
            return {
                'domain': {
                    'payment_method_line_id': [
                        ('payment_method_id.code', 'not in', restricted_providers)
                    ]
                }
            }
        return {}