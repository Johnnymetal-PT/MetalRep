# -*- coding: utf-8 -*-
from odoo import api, models
from odoo.exceptions import AccessError

# Models on which pg_product_multi_attachment defines the `attachment_ids`
# many2many-to-ir.attachment field. An attachment referenced by one of these
# records (that the current user may read) is considered readable.
_MA_MODELS = (
    'sale.order.line',
    'purchase.order.line',
    'product.product',
    'product.template',
)


def _domain_targets_ids(domain):
    """True if the search domain constrains specific attachment ids
    (e.g. ('id', 'in', [...])). The many2many_binary widget always reads its
    records this way; broad attachment searches do not, and are left untouched."""
    for leaf in domain:
        if isinstance(leaf, (list, tuple)) and len(leaf) == 3 and leaf[0] == 'id':
            return True
    return False


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def _pg_multi_attachment_allowed_ids(self, candidate_ids):
        """Among ``candidate_ids``, return the ids the current user may READ because
        the attachment is referenced by the ``attachment_ids`` m2m of a record the
        user can genuinely read.

        The reference searches run with the current user's own rights, so a record
        the user cannot see (e.g. another company's purchase.order.line) never
        grants access -> no cross-company data exposure.
        """
        candidate_ids = [i for i in candidate_ids if i]
        if not candidate_ids:
            return set()
        allowed = set()
        remaining = set(candidate_ids)
        for model_name in _MA_MODELS:
            if not remaining:
                break
            Model = self.env.get(model_name)
            if Model is None or 'attachment_ids' not in Model._fields:
                continue
            links = Model.search([('attachment_ids', 'in', list(remaining))])
            if not links:
                continue
            reachable = set(links.attachment_ids.ids) & remaining
            allowed |= reachable
            remaining -= reachable
        return allowed

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, access_rights_uid=None):
        # Only widen for regular users, and only for id-targeted reads (the widget).
        if self.env.is_superuser() or not _domain_targets_ids(domain):
            return super()._search(domain, offset, limit, order, access_rights_uid)

        standard = list(super()._search(domain, 0, None, order, access_rights_uid))
        standard_set = set(standard)
        # All ids matching the domain irrespective of access (bypasses the parent
        # filter via sudo -> is_superuser short-circuit above avoids recursion).
        all_matching = list(self.sudo()._search(domain, 0, None, order, access_rights_uid))
        extra_candidates = [i for i in all_matching if i not in standard_set]
        extra_allowed = self._pg_multi_attachment_allowed_ids(extra_candidates)
        if not extra_allowed:
            return super()._search(domain, offset, limit, order, access_rights_uid)

        keep = standard_set | extra_allowed
        merged = [i for i in all_matching if i in keep]
        merged = merged[offset:(offset + limit) if limit else None]
        return self.browse(merged)._as_query(order)

    def check(self, mode, values=None):
        try:
            return super().check(mode, values=values)
        except AccessError:
            # Only widen READ, and only via the multi-attachment reference path.
            if mode != 'read' or self.env.is_superuser():
                raise
            allowed = self._pg_multi_attachment_allowed_ids(self.ids)
            remaining = self.browse([i for i in self.ids if i not in allowed])
            if not remaining:
                return True
            # Re-run the standard check on what is genuinely not covered, so truly
            # private attachments still raise exactly as before.
            return super(IrAttachment, remaining).check(mode, values=values)
