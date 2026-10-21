# -*- coding: utf-8 -*-

from collections import defaultdict

from odoo import _, models
from odoo.exceptions import UserError


class PartnerLedgerReportHandler(models.AbstractModel):
    _inherit = "account.partner.ledger.report.handler"

    def _build_partner_lines(self, report, options, level_shift=0):
        lines = []

        totals_by_column_group = {
            column_group_key: {total: 0.0 for total in ["debit", "credit", "balance"]}
            for column_group_key in options["column_groups"]
        }

        partners_results = self._query_partners(options)
        initial_balances_by_partner = (
            self._get_initial_balance_values(
                [partner.id if partner else None for partner, _results in partners_results],
                options,
            )
            if partners_results
            else {}
        )

        search_filter = options.get("filter_search_bar", "")
        accept_unknown_in_filter = search_filter.lower() in self._get_no_partner_line_label().lower()
        for partner, results in partners_results:
            if options["export_mode"] == "print" and search_filter and not partner and not accept_unknown_in_filter:
                continue

            partner_key = partner.id if partner else None
            partner_initial_balance = initial_balances_by_partner.get(partner_key, {})
            partner_values = defaultdict(dict)
            for column_group_key in options["column_groups"]:
                partner_sum = results.get(column_group_key, {})
                initial_balance = partner_initial_balance.get(column_group_key, {})

                # Hide opening-balance amounts from the summary totals while keeping the
                # ending balance based on the full ledger history.
                partner_values[column_group_key]["debit"] = partner_sum.get("debit", 0.0) - initial_balance.get("debit", 0.0)
                partner_values[column_group_key]["credit"] = partner_sum.get("credit", 0.0) - initial_balance.get("credit", 0.0)
                partner_values[column_group_key]["balance"] = partner_sum.get("balance", 0.0)

                totals_by_column_group[column_group_key]["debit"] += partner_values[column_group_key]["debit"]
                totals_by_column_group[column_group_key]["credit"] += partner_values[column_group_key]["credit"]
                totals_by_column_group[column_group_key]["balance"] += partner_values[column_group_key]["balance"]

            lines.append(self._get_report_line_partners(options, partner, partner_values, level_shift=level_shift))

        return lines, totals_by_column_group

    def _report_expand_unfoldable_line_partner_ledger(
        self, line_dict_id, groupby, options, progress, offset, unfold_all_batch_data=None
    ):
        def init_progress_from_balance(balance_by_col_group):
            return {
                column_group_key: balance_by_col_group.get(column_group_key, {}).get("balance", 0)
                for column_group_key in options["column_groups"]
            }

        report = self.env.ref("account_reports.partner_ledger_report")
        markup, model, record_id = report._parse_line_id(line_dict_id)[-1]

        if model != "res.partner":
            raise UserError(_("Wrong ID for partner ledger line to expand: %s", line_dict_id))

        prefix_groups_count = 0
        for markup, dummy1, dummy2 in report._parse_line_id(line_dict_id):
            if markup.startswith("groupby_prefix_group:"):
                prefix_groups_count += 1
        level_shift = prefix_groups_count * 2

        lines = []

        # Keep the running balance seeded with the opening balance, but do not render
        # the synthetic initial-balance line itself.
        if offset == 0:
            if unfold_all_batch_data:
                init_balance_by_col_group = unfold_all_batch_data["initial_balances"][record_id]
            else:
                init_balance_by_col_group = self._get_initial_balance_values([record_id], options)[record_id]
            progress = init_progress_from_balance(init_balance_by_col_group)

        limit_to_load = report.load_more_limit + 1 if report.load_more_limit and options["export_mode"] != "print" else None

        if unfold_all_batch_data:
            aml_results = unfold_all_batch_data["aml_values"][record_id]
        else:
            aml_results = self._get_aml_values(options, [record_id], offset=offset, limit=limit_to_load)[record_id]

        has_more = False
        treated_results_count = 0
        next_progress = progress
        for result in aml_results:
            if options["export_mode"] != "print" and report.load_more_limit and treated_results_count == report.load_more_limit:
                has_more = True
                break

            new_line = self._get_report_line_move_line(
                options, result, line_dict_id, next_progress, level_shift=level_shift
            )
            lines.append(new_line)
            next_progress = {
                column["column_group_key"]: line_col.get("no_format", 0)
                for column, line_col in zip(options["columns"], new_line["columns"])
                if column["expression_label"] == "balance"
            }
            treated_results_count += 1

        return {
            "lines": lines,
            "offset_increment": treated_results_count,
            "has_more": has_more,
            "progress": next_progress,
        }
