"""Sanitiza a subscrição pública da newsletter (ver __manifest__.py)."""
from odoo import http
from odoo.http import request

# O nome da classe base do controller mudou entre versões do Odoo; tenta os dois.
try:
    from odoo.addons.website_mass_mailing.controllers.main import MassMailController as _BaseController
except ImportError:
    from odoo.addons.website_mass_mailing.controllers.main import WebsiteMassMailingController as _BaseController


class NewsletterSubscribePatch(_BaseController):
    @http.route('/website_mass_mailing/subscribe', type='json', auth='public', website=True)
    def subscribe(self, list_id, **post):
        # Lista branca: só estes campos do mailing.contact podem ser definidos pelo público.
        allowed_fields = {'email', 'name', 'x_studio_user_category', 'country_id'}
        passthrough = {'list_id', 'value', 'subscription_type', 'csrf_token'}

        # 1) Build a sanitized kwargs dict
        clean_post = {k: v for k, v in post.items() if k in allowed_fields and v}

        # normalize country
        if 'country_id' in clean_post:
            try:
                clean_post['country_id'] = int(clean_post['country_id'])
            except Exception:
                clean_post.pop('country_id', None)

        # parent expects these positional args
        value = (post.get('value') or clean_post.get('email') or '').strip()
        subscription_type = post.get('subscription_type') or 'email'

        # 2) Sanitize request.params (used by parent)
        params = request.params
        for k in list(params):
            if (not k) or (k not in allowed_fields and k not in passthrough):
                params.pop(k, None)
        params.update({'list_id': list_id, 'value': value, 'subscription_type': subscription_type})
        params.update(clean_post)

        # 3) Sanitize request.jsonrequest (also used by parent for type='json')
        jr = getattr(request, 'jsonrequest', None)
        if isinstance(jr, dict):
            for k in list(jr):
                if (not k) or (k not in allowed_fields and k not in passthrough):
                    jr.pop(k, None)
            jr.update({'list_id': list_id, 'value': value, 'subscription_type': subscription_type})
            jr.update(clean_post)

        # 4) Delegate to core handler with the clean kwargs only
        return super().subscribe(list_id, value, subscription_type, **clean_post)

