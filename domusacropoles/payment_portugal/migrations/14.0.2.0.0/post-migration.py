# Copyright 2021 Exo Software
import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    """A fix for the wrong simplified invoice AT code"""

    openupgrade.logged_query(
        env.cr,
        """
            UPDATE payment_acquirer
            SET multibanco_invoice = 'all'
            WHERE pt_pay_method = 'mb' AND
                  multibanco_auto_invoices = TRUE;
        """,
    )

    openupgrade.logged_query(
        env.cr,
        """
            UPDATE payment_acquirer
            SET multibanco_invoice = 'none'
            WHERE pt_pay_method = 'mb' AND
                  multibanco_auto_invoices = FALSE;
        """,
    )

    openupgrade.logged_query(
        env.cr,
        """
            UPDATE res_partner
            SET multibanco_invoice_off = TRUE
            WHERE multibanco_invoice_exception = TRUE;
        """,
    )
