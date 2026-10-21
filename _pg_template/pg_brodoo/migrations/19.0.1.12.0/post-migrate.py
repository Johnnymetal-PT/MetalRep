"""Remove a camada de "deliverable templates" (0 adocao em producao).

Ao remover os campos do modelo, o Odoo deixa as colunas na BD (nao as apaga
automaticamente), pelo que as removemos aqui por SQL. A tabela do M2M
project<->template tambem e removida. Nao ha migracao de dados: a entrega
continua a ser feita via project.milestone standard.
"""


def migrate(cr, version):
    if not version:
        return

    # Colunas orfas dos campos removidos em project.milestone.
    for column in (
        'pg_deliverable_template_ref',
        'pg_deliverable_phase',
        'pg_deliverable_priority',
    ):
        cr.execute('ALTER TABLE project_milestone DROP COLUMN IF EXISTS "%s"' % column)

    # Colunas orfas dos campos removidos em mail.activity.
    for column in (
        'pg_deliverable_cadence',
        'pg_deliverable_template_ref',
        'pg_deliverable_owner_id',
    ):
        cr.execute('ALTER TABLE mail_activity DROP COLUMN IF EXISTS "%s"' % column)

    # Tabela de relacao do M2M pg_committed_deliverable_template_ids.
    cr.execute('DROP TABLE IF EXISTS pg_project_committed_deliverable_rel')
