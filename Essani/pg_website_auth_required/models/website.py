"""Helpers de website para calcular a arvore publica autorizada a visitantes anonimos."""
from odoo import models

PUBLIC_ROOT_CATEGORY_PARAM = 'pg_website_auth_required.public_root_category_id'


class Website(models.Model):
    _inherit = 'website'

    def _pg_get_public_root_category_id(self):
        self.ensure_one()
        raw_value = self.env['ir.config_parameter'].sudo().get_param(
            PUBLIC_ROOT_CATEGORY_PARAM, '0'
        )
        try:
            return int(raw_value)
        except (TypeError, ValueError):
            return 0

    def _pg_get_public_allowed_category_ids(self):
        """Return the set of product.public.category ids that anonymous users
        are allowed to navigate in the shop: the configured root and all
        descendants. Empty set means no public category is allowed.
        """
        self.ensure_one()
        root_id = self._pg_get_public_root_category_id()
        if not root_id:
            return set()
        Category = self.env['product.public.category'].sudo()
        return set(Category.search([('id', 'child_of', root_id)]).ids)
