from ast import literal_eval
import logging

from odoo import _, api, models
from odoo.exceptions import MissingError, ValidationError
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class WebsiteSnippetFilter(models.Model):
    _inherit = "website.snippet.filter"

    _dynamic_snippet_limit_cap = 120

    def _get_dynamic_snippet_limit_cap(self):
        """Return the absolute maximum number of records a snippet can fetch."""

        return self._dynamic_snippet_limit_cap

    @api.constrains("limit")
    def _check_limit(self):
        """Allow a higher record limit for dynamic snippets."""

        for record in self:
            cap = record._get_dynamic_snippet_limit_cap()
            if not 0 < record.limit <= cap:
                raise ValidationError(_("The limit must be between 1 and %s.") % cap)

    def _prepare_values(self, limit=None, search_domain=None):
        """Gets the data and returns it in the right format for render."""

        self.ensure_one()

        cap = self._get_dynamic_snippet_limit_cap()
        baseline = min(16, cap)

        if limit:
            try:
                requested = int(limit)
            except (TypeError, ValueError):
                requested = 0
            limit = min(cap, max(baseline, requested))
        else:
            record_limit = min(self.limit or 0, cap) if self.limit else 0
            limit = max(record_limit, baseline)

        if self.filter_id:
            filter_sudo = self.filter_id.sudo()
            domain = filter_sudo._get_eval_domain()
            if "website_id" in self.env[filter_sudo.model_id]:
                domain = expression.AND([domain, self.env["website"].get_current_website().website_domain()])
            if "company_id" in self.env[filter_sudo.model_id]:
                website = self.env["website"].get_current_website()
                domain = expression.AND([domain, [("company_id", "in", [False, website.company_id.id])]])
            if "is_published" in self.env[filter_sudo.model_id]:
                domain = expression.AND([domain, [("is_published", "=", True)]])
            if search_domain:
                domain = expression.AND([domain, search_domain])
            try:
                records = self.env[filter_sudo.model_id].with_context(**literal_eval(filter_sudo.context)).search(
                    domain,
                    order=",".join(literal_eval(filter_sudo.sort)) or None,
                    limit=limit,
                )
                return self._filter_records_to_values(records)
            except MissingError:
                _logger.warning(
                    "The provided domain %s in 'ir.filters' generated a MissingError in '%s'",
                    domain,
                    self._name,
                )
                return []
        elif self.action_server_id:
            try:
                return (
                    self.action_server_id.with_context(
                        dynamic_filter=self,
                        limit=limit,
                        search_domain=search_domain,
                    )
                    .sudo()
                    .run()
                    or []
                )
            except MissingError:
                _logger.warning(
                    "The provided domain %s in 'ir.actions.server' generated a MissingError in '%s'",
                    search_domain,
                    self._name,
                )
                return []
