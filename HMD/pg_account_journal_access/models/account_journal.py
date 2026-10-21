# -*- coding: utf-8 -*-
"""Whitelist de utilizadores por diario contabilistico.

Combinado com as `ir.rule` GLOBAIS em
`security/journal_access_rules.xml`, este modelo restringe o acesso
a `account.journal`, `account.move` e `account.move.line` quando o
diario tem utilizadores definidos em `pg_allowed_user_ids`.

A flag `pg_access_seeded` evita que os Admins Contab. sejam
re-adicionados depois de removidos deliberadamente.

Ver `__manifest__.py` para o guia completo.
"""

from odoo import api, fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    pg_allowed_user_ids = fields.Many2many(
        comodel_name="res.users",
        relation="pg_account_journal_allowed_users_rel",
        column1="journal_id",
        column2="user_id",
        string="Utilizadores com acesso",
        domain=[("share", "=", False)],
        help="Lista de PERMITIDOS (whitelist), apenas utilizadores internos.\n"
             "- Vazio: o diário fica aberto a todos os utilizadores de contabilidade.\n"
             "- Com utilizadores: apenas estes podem ver, criar, editar e lançar neste diário.\n"
             "Ao restringir pela primeira vez, os Administradores de Contabilidade são "
             "pré-preenchidos automaticamente, mas podem ser removidos.",
    )
    # Campo técnico: marca que os administradores já foram pré-preenchidos nesta lista,
    # para não voltarem a ser adicionados depois de o utilizador os remover de propósito.
    pg_access_seeded = fields.Boolean(
        string="Acesso pré-preenchido",
        default=False,
        copy=False,
    )

    @api.onchange("pg_allowed_user_ids")
    def _onchange_pg_allowed_user_ids(self):
        """Ao restringir um diário, pré-preencher os Administradores de Contabilidade.

        Mantém-se removível: depois de pré-preenchidos, o utilizador pode tirar quem
        quiser sem que sejam re-adicionados. Se a lista for esvaziada (volta a 'aberto
        a todos'), o pré-preenchimento fica de novo disponível para a próxima restrição.
        """
        manager_group = self.env.ref(
            "account.group_account_manager", raise_if_not_found=False
        )
        for journal in self:
            if journal.pg_allowed_user_ids and not journal.pg_access_seeded:
                if manager_group:
                    # Apenas administradores internos (exclui eventuais utilizadores share).
                    internal_managers = manager_group.users.filtered(
                        lambda u: not u.share
                    )
                    journal.pg_allowed_user_ids |= internal_managers
                journal.pg_access_seeded = True
            elif not journal.pg_allowed_user_ids and journal.pg_access_seeded:
                journal.pg_access_seeded = False
