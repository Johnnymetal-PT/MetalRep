# controllers/main.py
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale

class WebsiteShopRedirect(http.Controller):

    @http.route(['/shop'], type='http', auth="public", website=True)
    def shop_redirect(self, **kw):
        if not request.env.user or request.env.user._is_public():
            # User is not logged in, redirect to the login page
            return request.redirect('/web/login')  # Redirect to login page
            # Uncomment the next line to redirect to the home page instead
            # return request.redirect('/')
        
        # If the user is logged in, call the WebsiteSale controller's shop method
        return WebsiteSale().shop()
