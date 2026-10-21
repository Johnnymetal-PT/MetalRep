from odoo import http
from odoo.http import request

class CustomWishlistController(http.Controller):

    @http.route(['/custom/wishlist'], type='http', auth="public", website=True)
    def custom_wishlist_page(self, **post):
        """ Custom route to render the wishlist page without redirection """
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

