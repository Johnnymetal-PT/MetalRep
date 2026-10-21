"""
Script de pos-migracao da versao 1.9.1 do modulo legacy pg_phc_api_old.

Modulo: pg_phc_api_old.
Ficheiro: pg_phc_api_old\migrations\1.9.1\post-migrate.py.
Executa ajustes apos upgrade para manter coerencia tecnica.
"""

from odoo import api, SUPERUSER_ID

from ..hooks import ensure_phc_partner_columns, ensure_phc_partner_fields


def migrate(cr, version):
    """Recreate PHC partner columns that may be missing.

    Some databases were deployed without the ``x_studio_*`` columns, causing
    runtime ``UndefinedColumn`` errors when reading partners. This migration
    re-adds the columns and recreates the Studio field metadata so the ORM can
    access them safely.
    """

    ensure_phc_partner_columns(cr)

    env = api.Environment(cr, SUPERUSER_ID, {})
    ensure_phc_partner_fields(env)

