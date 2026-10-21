"""Post-migration hooks for pg_brodoo 19.0.1.2.0."""


def migrate(cr, version):
    """Enable effort sync by default for existing projects."""
    cr.execute(
        """
        UPDATE project_project
           SET pg_effort_sync_enabled = TRUE
         WHERE COALESCE(pg_effort_sync_enabled, FALSE) = FALSE
        """
    )
    return
