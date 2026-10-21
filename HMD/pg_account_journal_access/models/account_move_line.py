# -*- coding: utf-8 -*-
"""Diagnostico de falhas de acesso em rubricas contabilisticas PG."""

import logging

from odoo import models


_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _check_access(self, operation):
        result = super()._check_access(operation)
        if operation == "create" and result:
            forbidden_records = result[0]
            pg_rules = self.env["ir.rule"]._get_failing(
                forbidden_records, mode=operation
            ).sudo().filtered(lambda rule: rule.name == "PG: Acesso a rubricas por diário")
            if pg_rules:
                self._pg_log_journal_access_denial(forbidden_records, pg_rules)
        return result

    def _pg_log_journal_access_denial(self, forbidden_records, pg_rules):
        """Log detalhado antes de o Odoo levantar o AccessError standard."""
        user = self.env.user
        records = forbidden_records.sudo()
        move_ids = records.mapped("move_id")
        journal_ids = move_ids.mapped("journal_id")
        groups = user.groups_id.sudo()
        group_external_ids = groups.get_external_id()

        lines_payload = []
        for line in records:
            move = line.move_id
            journal = move.journal_id
            allowed_users = journal.pg_allowed_user_ids
            lines_payload.append({
                "line_id": line.id,
                "line_name": line.display_name,
                "move_id": move.id,
                "move_name": move.name,
                "move_type": move.move_type,
                "move_state": move.state,
                "move_company": move.company_id.display_name,
                "journal_id": journal.id,
                "journal_name": journal.display_name,
                "journal_type": journal.type,
                "journal_company": journal.company_id.display_name,
                "journal_allowed_user_ids": allowed_users.ids,
                "journal_allowed_user_names": allowed_users.mapped("display_name"),
                "journal_is_open": not bool(allowed_users),
                "current_user_in_journal_whitelist": user.id in allowed_users.ids,
                "current_user_allowed_by_pg_rule": (
                    not bool(allowed_users) or user.id in allowed_users.ids
                ),
            })

        _logger.warning(
            "PG journal access denied on account.move.line create | "
            "uid=%s user=%s login=%s company=%s allowed_companies=%s "
            "groups=%s context_keys=%s default_move_type=%s default_journal_id=%s "
            "default_purchase_id=%s active_model=%s active_id=%s "
            "failing_rule_ids=%s failing_rule_domains=%s "
            "forbidden_line_ids=%s move_ids=%s journal_ids=%s payload=%s",
            user.id,
            user.display_name,
            user.login,
            self.env.company.display_name,
            self.env.companies.mapped("display_name"),
            [
                group_external_ids.get(group.id) or group.display_name
                for group in groups
            ],
            sorted(self.env.context.keys()),
            self.env.context.get("default_move_type"),
            self.env.context.get("default_journal_id"),
            self.env.context.get("default_purchase_id"),
            self.env.context.get("active_model"),
            self.env.context.get("active_id"),
            pg_rules.ids,
            pg_rules.mapped("domain_force"),
            records.ids,
            move_ids.ids,
            journal_ids.ids,
            lines_payload,
        )
