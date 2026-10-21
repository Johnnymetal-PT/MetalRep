import logging

from odoo import SUPERUSER_ID, api


_logger = logging.getLogger(__name__)


def _column_exists(cr, table_name, column_name):
    cr.execute(
        """
        SELECT 1
          FROM information_schema.columns
         WHERE table_name = %s
           AND column_name = %s
        """,
        (table_name, column_name),
    )
    return bool(cr.fetchone())


def migrate(cr, version):
    if not all(
        _column_exists(cr, "res_users", column_name)
        for column_name in ("phc_api_base_url", "phc_api_user", "phc_api_password")
    ):
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    company_model = env["res.company"].sudo()

    cr.execute(
        """
        SELECT company_id, id, phc_api_base_url, phc_api_user, phc_api_password
          FROM res_users
         WHERE company_id IS NOT NULL
           AND (
               phc_api_base_url IS NOT NULL
               OR phc_api_user IS NOT NULL
               OR phc_api_password IS NOT NULL
           )
         ORDER BY company_id, id
        """
    )

    grouped_values = {}
    for company_id, user_id, base_url, username, password in cr.fetchall():
        company_values = grouped_values.setdefault(
            company_id,
            {
                "phc_api_base_url": "",
                "phc_api_user": "",
                "phc_api_password": "",
                "source_user_id": user_id,
            },
        )
        for field_name, value in (
            ("phc_api_base_url", base_url or ""),
            ("phc_api_user", username or ""),
            ("phc_api_password", password or ""),
        ):
            if value and not company_values[field_name]:
                company_values[field_name] = value
            elif value and company_values[field_name] and company_values[field_name] != value:
                _logger.warning(
                    "PHC credential conflict while migrating company %s. Keeping value from user %s and ignoring value from user %s for %s.",
                    company_id,
                    company_values["source_user_id"],
                    user_id,
                    field_name,
                )

    for company_id, values in grouped_values.items():
        company = company_model.browse(company_id)
        if not company.exists():
            continue

        write_vals = {}
        for field_name in ("phc_api_base_url", "phc_api_user", "phc_api_password"):
            if not company[field_name] and values[field_name]:
                write_vals[field_name] = values[field_name]

        if write_vals:
            company.write(write_vals)
