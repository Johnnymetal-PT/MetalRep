# -*- coding: utf-8 -*-
"""O modelo pg.planeamento.semana deixou de ser uma vista SQL (_auto=False) e passou
a ser um modelo real (tabela). É preciso largar a VIEW antiga antes de o ORM tentar
criar a tabela com o mesmo nome, senão há conflito de relação no PostgreSQL.
"""


def migrate(cr, version):
    cr.execute("DROP VIEW IF EXISTS pg_planeamento_semana CASCADE")
