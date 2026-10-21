# -*- coding: utf-8 -*-
"""Migracao de visibilidade de menus apos re-gate (CRM e Despesas).

Dois menus standard sao re-gated por este modulo:
  - crm.crm_menu_root          -> pg_group_crm_visible
  - hr_expense.menu_hr_expense_root -> pg_group_expenses_visible

Para NAO esconder estes menus de quem hoje os ve, este hook copia para os
grupos novos os utilizadores que atualmente os veem:
  - CRM: membros atuais de sales_team.group_sale_salesman / group_sale_manager
  - Despesas: o menu nao tinha grupo (visivel a todos) -> todos os utilizadores
    internos ativos

Exclusao dos utilizadores-alvo (ex.: "BD Geral User"):
  define-se o parametro de sistema (Definicoes Tecnicas > Parametros do Sistema)
      pg_bd_geral_security.excluded_user_logins = login1,login2
  ANTES de instalar/atualizar o modulo. Esses logins ficam fora da migracao e,
  por isso, deixam de ver CRM e Despesas.

Odoo 17: a assinatura do post_init_hook recebe `env`.
"""
import logging

_logger = logging.getLogger(__name__)


def _excluded_users(env):
    raw = env["ir.config_parameter"].sudo().get_param(
        "pg_bd_geral_security.excluded_user_logins", default=""
    )
    logins = [l.strip() for l in (raw or "").split(",") if l.strip()]
    if not logins:
        _logger.warning(
            "[pg_bd_geral_security] Parametro 'excluded_user_logins' vazio: "
            "nenhum utilizador sera excluido da migracao CRM/Despesas. "
            "Confirme se o BD Geral User deve ficar de fora."
        )
        return env["res.users"]
    return env["res.users"].sudo().search([("login", "in", logins)])


def _migrate(group, users, label):
    if not group:
        _logger.warning("[pg_bd_geral_security] grupo %s nao encontrado; migracao ignorada.", label)
        return
    users = users.filtered(lambda u: u.active and not u.share)
    if users:
        group.sudo().write({"users": [(4, uid) for uid in users.ids]})
    _logger.info("[pg_bd_geral_security] %s: migrados %s utilizadores.", label, len(users))


def post_init_hook(env):
    excluded = _excluded_users(env)

    # --- CRM: quem ve CRM hoje = membros dos grupos de Vendas ---
    crm_visible = env.ref("pg_bd_geral_security.pg_group_crm_visible", raise_if_not_found=False)
    sale_groups = env["res.groups"]
    for xmlid in ("sales_team.group_sale_salesman", "sales_team.group_sale_manager"):
        grp = env.ref(xmlid, raise_if_not_found=False)
        if grp:
            sale_groups |= grp
    crm_users = sale_groups.mapped("users") - excluded
    _migrate(crm_visible, crm_users, "CRM")

    # --- Despesas: menu era visivel a todos -> todos os utilizadores internos ---
    expenses_visible = env.ref("pg_bd_geral_security.pg_group_expenses_visible", raise_if_not_found=False)
    internal_users = env["res.users"].sudo().search([("share", "=", False), ("active", "=", True)])
    expenses_users = internal_users - excluded
    _migrate(expenses_visible, expenses_users, "Despesas")
