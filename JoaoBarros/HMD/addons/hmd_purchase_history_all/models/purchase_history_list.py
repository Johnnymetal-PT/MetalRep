import logging
import re

from odoo import models, tools


_logger = logging.getLogger(__name__)


class PurchaseHistoryList(models.Model):
    _inherit = "purchase.history.list"

    def init(self):
        super_init = getattr(super(), "init", None)
        if super_init:
            super_init()
        self._relax_state_filter()

    def _relax_state_filter(self):
        _logger.info("Preparing to relax purchase history state filter on view %s", self._table)
        self.env.cr.execute("SELECT pg_get_viewdef(%s, true)", (self._table,))
        result = self.env.cr.fetchone()
        if not result:
            _logger.warning(
                "Could not retrieve the SQL definition for view %s; keeping the original definition",
                self._table,
            )
            return

        view_query = result[0]
        _logger.debug("Original purchase history SQL for %s: %s", self._table, view_query)

        patterns = [
            r"COALESCE\(\s*(?:(?:\"?po\"?|\"?purchase_order\"?)\.)?\"?state\"?[^\)]*\)\s+(?:NOT\s+)?IN\s*\([^\)]*\)",
            r"(?:(?:\"?po\"?|\"?purchase_order\"?)\.)\"?state\"?\s+(?:NOT\s+)?IN\s*\([^\)]*\)",
            r"\"?state\"?\s+(?:NOT\s+)?IN\s*\([^\)]*\)",
            r"(?:(?:\"?po\"?|\"?purchase_order\"?)\.)\"?state\"?\s*(?:=|!=|<>|<=|>=)\s*(?:\([^\)]*\)|'[^']*'|\"[^\"]*\"|\w+)",
            r"\"?state\"?\s*(?:=|!=|<>|<=|>=)\s*(?:\([^\)]*\)|'[^']*'|\"[^\"]*\"|\w+)",
        ]

        def _replace_with_true(match):
            matched_text = match.group(0)
            _logger.debug(
                "Matched state filter fragment on %s: %s",
                self._table,
                matched_text,
            )
            return "TRUE"

        new_view_query = view_query
        total_replacements = 0
        for pattern in patterns:
            new_view_query, replacements = re.subn(
                pattern,
                _replace_with_true,
                new_view_query,
                flags=re.IGNORECASE | re.MULTILINE,
            )
            total_replacements += replacements
            if replacements:
                _logger.info(
                    "Applied pattern %s on %s; replacements=%s",
                    pattern,
                    self._table,
                    replacements,
                )

        if total_replacements == 0:
            _logger.warning(
                "No state filter found for view %s. SQL remains unchanged: %s",
                self._table,
                view_query,
            )
            return

        _logger.debug(
            "Updated purchase history SQL for %s: %s",
            self._table,
            new_view_query,
        )

        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"CREATE OR REPLACE VIEW {self._table} AS {new_view_query}")
        _logger.info(
            "Recreated purchase history view %s without state filter (removed %s occurrence(s))",
            self._table,
            total_replacements,
        )
