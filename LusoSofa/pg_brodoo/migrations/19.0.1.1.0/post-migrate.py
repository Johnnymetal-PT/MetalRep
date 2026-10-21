"""Post-migration hooks for pg_brodoo 19.0.1.1.0."""


def migrate(cr, version):
    """No-op migration.

    Campo pg_project_key é Char nullable, sem necessidade de backfill.
    """
    return
