# -*- coding: utf-8 -*-
"""Limpeza das ir.actions.server orfas do botao smart "Projetos".

A partir da versao 18.0.1.1.0 os botoes passam a usar type="object"
chamando diretamente `action_view_related_projects`. As server actions
intermedias (e a logica `_ensure_project_server_actions` que as
recriava) deixam de existir; este post-migrate remove os registos que
tenham ficado na base, de forma idempotente.

A remocao por XID e tambem garantida pelo orphan-removal standard do
Odoo (registos noupdate=False retirados do data file). Esta migracao e
a salvaguarda explicita.
"""

from odoo import SUPERUSER_ID, api

_XMLIDS = (
    "hmd_product_project_button.product_template_project_server_action",
    "hmd_product_project_button.product_product_project_server_action",
)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for xml_id in _XMLIDS:
        action = env.ref(xml_id, raise_if_not_found=False)
        if action:
            action.sudo().unlink()
