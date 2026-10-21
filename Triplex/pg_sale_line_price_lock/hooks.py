# -*- coding: utf-8 -*-
"""Reatribui o grupo de preços só leitura aos utilizadores que já o tinham em produção.

Desinstalar o módulo apaga o grupo e, com ele, as associações. Ao reinstalar, este hook
volta a pôr os mesmos utilizadores (identificados pelo login) no grupo.
"""
import logging

_logger = logging.getLogger(__name__)

# Utilizadores bloqueados em produção à data de 2026-10-08.
LOCKED_USER_LOGINS = [
    "ananunes@casamagna.eu",
    "marketing@casamagna.eu",
    "joelsoares@triplexgroup.pt",
    "producao@oficinna22.pt",
    "sylvie@casamagna.eu",
]


def post_init_hook(env):
    group = env.ref("pg_sale_line_price_lock.group_sale_line_price_readonly")
    # active_test=False: um utilizador arquivado volta bloqueado se for reativado.
    users = env["res.users"].with_context(active_test=False).search(
        [("login", "in", LOCKED_USER_LOGINS)]
    )
    users.write({"groups_id": [(4, group.id)]})
    missing = set(LOCKED_USER_LOGINS) - set(users.mapped("login"))
    if missing:
        _logger.warning(
            "pg_sale_line_price_lock: utilizadores não encontrados nesta BD: %s",
            ", ".join(sorted(missing)),
        )
