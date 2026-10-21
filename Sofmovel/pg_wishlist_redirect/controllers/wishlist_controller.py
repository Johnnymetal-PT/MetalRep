"""Controller `/custom/wishlist` que evita o redirect para /shop em wishlist vazia.

Pertence ao modulo `pg_wishlist_redirect`. Endpoint alternativo ao
`/shop/wishlist`; quando vazio renderiza o template com lista vazia e
`empty_message` em vez de redirecionar.
"""
from odoo import http
from odoo.http import request

class CustomWishlistController(http.Controller):
    """Endpoint publico que renderiza a wishlist mesmo quando esta vazia."""

    @http.route(['/custom/wishlist'], type='http', auth="public", website=True)
    def custom_wishlist_page(self, **post):
        """Renderiza `website_sale_wishlist.product_wishlist` sem redirect.

        Auth=public mas exige `partner_id` (utilizador autenticado); anonimo
        e enviado para `/web/login`.
        """
        partner = request.env.user.partner_id
        if not partner:
            return request.redirect('/web/login')  # Ensure the user is logged in

        ProductWishlist = request.env['product.wishlist']
        wishlist_items = ProductWishlist.sudo().search([
            ('partner_id', '=', partner.id)
        ])

        # Render the wishlist page with all items or an empty message
        return request.render("website_sale_wishlist.product_wishlist", {
            'wishes': wishlist_items,
            'empty_message': "Your wishlist is currently empty."
        })

