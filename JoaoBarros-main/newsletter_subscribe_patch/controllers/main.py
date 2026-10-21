"""Sanitize newsletter subscription payloads.

This controller wraps the default newsletter subscribe endpoint to drop
any blank or unexpected fields from the request before deferring to the
standard implementation. This avoids invalid domains with empty field
names and ensures the NAME, COUNTRY and USER CATEGORY fields map to
their corresponding mailing.contact fields.
"""

from odoo import http
from odoo.http import request

try:  # Odoo 16+
    from odoo.addons.website_mass_mailing.controllers.main import MassMailController as _BaseController
except ImportError:  # Fall back for older Odoo versions
    from odoo.addons.website_mass_mailing.controllers.main import WebsiteMassMailingController as _BaseController


class NewsletterSubscribePatch(_BaseController):
    @http.route('/website_mass_mailing/subscribe', type='json', auth='public', website=True)
    def subscribe(self, list_id, **post):
        """Filter incoming data and delegate to the original handler."""
        allowed = {'email', 'name', 'x_studio_user_category', 'country_id'}
        clean_post = {k: v for k, v in post.items() if k in allowed and v}

        # Strip any spurious or empty keys from the global request params so
        # the core controller does not build invalid search domains.
        params = request.params
        bad_keys = [
            k
            for k in list(params)
            if not k
            or (k not in allowed and k not in {'list_id', 'value', 'subscription_type', 'csrf_token'})
        ]
        for k in bad_keys:
            params.pop(k, None)
        params.update(clean_post)

        # ``subscribe`` expects ``value`` (the email) and ``subscription_type``
        # as positional arguments. Preserve them from the raw payload or fall
        # back to sensible defaults based on the sanitized data.
        value = post.get('value') or clean_post.get('email')
        subscription_type = post.get('subscription_type') or 'email'

        return super().subscribe(list_id, value, subscription_type, **clean_post)
