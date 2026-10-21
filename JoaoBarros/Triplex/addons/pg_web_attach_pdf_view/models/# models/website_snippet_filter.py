# models/website_snippet_filter.py
from odoo import models, api, _
from odoo.exceptions import ValidationError

class WebsiteSnippetFilter(models.Model):
    _inherit = 'website.snippet.filter'

    @api.constrains('limit')
    def _check_limit(self):
        # Pick a sane upper bound for your site. 120 is usually fine.
        MAX = 120
        for record in self:
            if not 0 < record.limit <= MAX:
                raise ValidationError(_("The limit must be between 1 and %s.", MAX))
