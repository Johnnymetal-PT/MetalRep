"""Post-migration hooks for pg_brodoo 19.0.1.5.0."""


def migrate(cr, version):
    """Adoption metrics are database-wide; no data migration is required."""
    return
