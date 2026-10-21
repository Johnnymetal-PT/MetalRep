# controllers/main.py
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale

class WebsiteOrderBypass(WebsiteSale):

    @http.route(['/shop/confirm_order'], type='http', auth="public", website=True)
    def confirm_order(self, **post):
        order = request.website.sale_get_order()
        if not order:
            return request.redirect('/shop')
        
        # Confirm the order without requiring immediate payment
        order.action_confirm()

        # Generate invoice for the order
        if order._get_invoicing_policy() == 'order':
            order._create_invoices()

        # Send order confirmation email to the customer
        template = request.env.ref('sale.email_template_edi_sale')
        if template:
            template.sudo().send_mail(order.id, force_send=True)

        # Redirect to order confirmation page
        return request.redirect('/shop/confirmation')
