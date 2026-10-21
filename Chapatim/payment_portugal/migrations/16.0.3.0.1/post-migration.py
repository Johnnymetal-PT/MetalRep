# Copyright 2021 Exo Software
import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    company_ids = (
        env["res.company"].search([]).filtered(lambda c: c.country_code == "PT")
    )

    for company in company_ids:
        mb_payment_provider = env["payment.provider"].search(
            [
                ("company_id", "=", company.id),
                ("provider", "in", ["eupago", "ifthenpay"]),
                ("pt_pay_method", "=", "mb"),
                ("state", "!=", "disabled"),
            ],
            limit=1,
        )

        company.write({"l10n_pt_mb_payment_provider": mb_payment_provider.id})
