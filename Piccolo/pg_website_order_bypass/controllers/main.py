"""Override do checkout para confirmar a SO sem exigir pagamento online.

A Piccolo nao cobra online; o checkout do website e usado apenas
como entrada de encomenda. Este controller substitui o passo de
pagamento por uma confirmacao direta + fatura (se politica `order`) +
email de confirmacao.
"""
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteOrderBypass(WebsiteSale):

    @http.route(['/shop/confirm_order'], type='http', auth="public", website=True)
    def confirm_order(self, **post):
        # Carrinho atual do utilizador (logado ou publico via cookie).
        order = request.website.sale_get_order()
        if not order:
            return request.redirect('/shop')

        # Confirma a SO sem passar pelo provider de pagamento.
        order.action_confirm()

        # Fatura imediata so faz sentido se a politica de faturacao do
        # produto for "ao confirmar" (``order``). Em politica
        # ``delivery`` a fatura sai depois do picking - nao tocar aqui.
        if order._get_invoicing_policy() == 'order':
            order._create_invoices()

        # ``sudo()`` necessario porque o checkout pode estar a correr como
        # utilizador publico (sem permissoes para envio de mail).
        template = request.env.ref('sale.email_template_edi_sale')
        if template:
            template.sudo().send_mail(order.id, force_send=True)

        return request.redirect('/shop/confirmation')
