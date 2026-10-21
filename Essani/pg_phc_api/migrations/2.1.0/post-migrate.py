"""Migration for pg_phc_api 2.1.0 — apply default PHC user mapping.

Delegates to ``apply_pg_phc_responsavel_interno_defaults`` so that the exact
same idempotent logic runs both here (during upgrades) and from the module's
``post_init_hook`` (on fresh installs). The shared function:

* never touches the ORM (pure SQL) — no PHC sync is ever triggered;
* only overwrites ``pg_phc_responsavel_interno_name`` when it is empty OR
  equal to the legacy cleaned ``res.users.name`` (i.e. the value the previous
  2.0.8 migration seeded blindly). Manual edits done by admins are preserved.
"""

import logging


_logger = logging.getLogger(__name__)


def migrate(cr, version):
    from odoo.addons.pg_phc_api.models.res_partner import (
        apply_pg_phc_responsavel_interno_defaults,
    )

    updated = apply_pg_phc_responsavel_interno_defaults(cr)
    _logger.info(
        "pg_phc_api 2.1.0 migration: applied PHC user mapping defaults; "
        "%s user rows updated.",
        updated,
    )
