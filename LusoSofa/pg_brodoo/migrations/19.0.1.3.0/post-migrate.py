"""Post-migration hooks for pg_brodoo 19.0.1.3.0."""


def migrate(cr, version):
    """No-op migration for automatic effort sync triggers."""
    return
