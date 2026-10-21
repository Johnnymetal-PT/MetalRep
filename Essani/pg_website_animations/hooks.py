# -*- coding: utf-8 -*-
"""Liga a folha de estilos e o script ao website escolhido, e só a esse.

Porque é um hook e não a chave `assets` do manifesto: declarados no manifesto, os
ficheiros entram no bundle de **todos** os websites da base — e esta base tem cinco.
Aqui o asset nasce com `website_id` preenchido; e se o website não existir, não se
cria nada, em vez de se criar um asset sem website, que valeria para todos.
"""

import logging

_logger = logging.getLogger(__name__)

PARAM_WEBSITE = "pg_website_animations.website_name"
WEBSITE_POR_OMISSAO = "Essani V4"
MODULO = "pg_website_animations"

ASSETS = [
    ("asset_css", "Animações (CSS)", "static/src/css/pg_animations.css"),
    ("asset_js", "Animações (entrada ao scroll)", "static/src/js/pg_reveal.js"),
]


def _website_alvo(env):
    nome = env["ir.config_parameter"].sudo().get_param(
        PARAM_WEBSITE, WEBSITE_POR_OMISSAO)
    return env["website"].search([("name", "=", nome)], limit=1)


def post_init_criar_assets(env):
    website = _website_alvo(env)
    if not website:
        _logger.warning(
            "pg_website_animations: não existe nenhum website com o nome pretendido; "
            "não se liga nada. Defina o parâmetro %s e reinstale.", PARAM_WEBSITE)
        return

    for sufixo, titulo, caminho in ASSETS:
        xmlid = "%s.%s" % (MODULO, sufixo)
        if env.ref(xmlid, raise_if_not_found=False):
            continue
        asset = env["ir.asset"].create({
            "name": "%s: %s" % (MODULO, titulo),
            "bundle": "web.assets_frontend",
            "directive": "append",
            "path": "%s/%s" % (MODULO, caminho),
            "website_id": website.id,
        })
        # Com xmlid do módulo, o asset desaparece quando o módulo é desinstalado.
        env["ir.model.data"]._update_xmlids([{
            "xml_id": xmlid, "record": asset, "noupdate": False}])
    _logger.info("pg_website_animations: assets ligados ao website '%s' (id %s).",
                 website.name, website.id)
