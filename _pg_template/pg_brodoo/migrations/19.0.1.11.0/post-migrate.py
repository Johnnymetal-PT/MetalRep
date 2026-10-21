"""Converte a ligacao Odoo flat (campos pg_odoo_* no repositorio) numa
pg.odoo.connection com purpose='production', e limpa as colunas orfas.

Ao remover os campos do modelo, o Odoo deixa as colunas na BD (nao as apaga
automaticamente), pelo que as lemos aqui por SQL antes de as remover.
"""
from odoo import SUPERUSER_ID, api

_FLAT_COLUMNS = (
    'pg_adoption_enabled',
    'pg_odoo_project_key',
    'pg_odoo_base_url',
    'pg_odoo_database',
    'pg_odoo_login',
    'pg_odoo_api_key',
    'pg_template_ref',
    'pg_adoption_last_sync_at',
    'pg_adoption_last_sync_status',
)


def migrate(cr, version):
    if not version:
        return

    # Idempotencia: se a coluna base ja foi removida, nada a fazer.
    cr.execute(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = 'pg_ai_repository' AND column_name = 'pg_odoo_base_url'"
    )
    if not cr.fetchone():
        return

    cr.execute(
        """
        SELECT id, pg_odoo_base_url, pg_odoo_database, pg_odoo_login, pg_odoo_api_key
        FROM pg_ai_repository
        WHERE COALESCE(TRIM(pg_odoo_base_url), '') != ''
        """
    )
    rows = cr.fetchall()

    env = api.Environment(cr, SUPERUSER_ID, {})
    connection_model = env['pg.odoo.connection']
    for repo_id, base_url, database, login, api_key in rows:
        already = connection_model.search_count(
            [('repository_id', '=', repo_id), ('purpose', '=', 'production')]
        )
        if already:
            continue
        connection_model.create({
            'repository_id': repo_id,
            'purpose': 'production',
            'base_url': base_url,
            'database': database or False,
            'login': login or False,
            'api_key': api_key or False,
        })

    # Limpar as colunas orfas dos campos removidos.
    for column in _FLAT_COLUMNS:
        cr.execute('ALTER TABLE pg_ai_repository DROP COLUMN IF EXISTS "%s"' % column)
