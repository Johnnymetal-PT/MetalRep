# -*- coding: utf-8 -*-
"""Liga o motor das cenas ao website escolhido, e só a esse, e cria a página de demonstração.

Os assets nascem com `website_id` preenchido (e não na chave `assets` do manifesto, que os
aplicaria a todos os websites da base). Se o website não existir não se cria nada: um asset
sem website valeria para todos.
"""

import logging

from odoo.tools import file_open

_logger = logging.getLogger(__name__)

PARAM_WEBSITE = "pg_website_scroll_scenes.website_name"
WEBSITE_POR_OMISSAO = "Essani V5"
MODULO = "pg_website_scroll_scenes"
URL_DEMO = "/cenas-scroll"

# A ordem conta: o GSAP antes do ScrollTrigger, e os dois antes do motor.
ASSETS = [
    ("asset_gsap", "GSAP", "static/lib/gsap/gsap.min.js", 10),
    ("asset_scrolltrigger", "ScrollTrigger", "static/lib/gsap/ScrollTrigger.min.js", 11),
    ("asset_css", "Cenas (CSS)", "static/src/css/pg_scenes.css", 12),
    ("asset_js", "Cenas (motor)", "static/src/js/pg_scenes.js", 13),
]


def _website_alvo(env):
    nome = env["ir.config_parameter"].sudo().get_param(
        PARAM_WEBSITE, WEBSITE_POR_OMISSAO)
    return env["website"].search([("name", "=", nome)], limit=1)


def _criar_asset(env, website, sufixo, titulo, caminho, sequencia):
    xmlid = "%s.%s" % (MODULO, sufixo)
    asset = env.ref(xmlid, raise_if_not_found=False)
    if not asset:
        asset = env["ir.asset"].create({
            "name": "%s: %s" % (MODULO, titulo),
            "bundle": "web.assets_frontend",
            "directive": "append",
            "path": "%s/%s" % (MODULO, caminho),
            "sequence": sequencia,
            "website_id": website.id,
        })
    # Com xmlid do módulo, o asset desaparece quando o módulo é desinstalado.
    # `noupdate=True` e `update=True`: sem isto o Odoo trata o registo como órfão (não vem
    # de nenhum ficheiro de dados) e apaga-o ao atualizar o módulo, deixando o website sem
    # CSS nem JS. Corre também em registos que já existem, para os proteger.
    env["ir.model.data"]._update_xmlids([{
        "xml_id": xmlid, "record": asset, "noupdate": True}], update=True)


def garantir_assets(env):
    """Cria o que falte dos assets do website escolhido (usado nas migrações)."""
    website = _website_alvo(env)
    if not website:
        return
    for sufixo, titulo, caminho, sequencia in ASSETS:
        _criar_asset(env, website, sufixo, titulo, caminho, sequencia)


def _ler_arch():
    # Em modo texto o file_open já força UTF-8 (e não aceita o argumento `encoding`).
    with file_open("%s/data/demo_page_arch.xml" % MODULO) as f:
        return f.read()


def atualizar_pagina_demo(env):
    """Repõe a página de demonstração com o conteúdo do ficheiro (usado nas migrações).

    Se a página não existir, cria-a. Se existir, reescreve só o arch: o URL e a
    publicação ficam como estão.
    """
    website = _website_alvo(env)
    if not website:
        return
    pagina = env["website.page"].search([
        ("url", "=", URL_DEMO), ("website_id", "=", website.id)], limit=1)
    if pagina:
        pagina.write({"arch": _ler_arch()})
    else:
        _criar_pagina_demo(env, website)


def _criar_pagina_demo(env, website):
    xmlid = "%s.demo_page" % MODULO
    if env.ref(xmlid, raise_if_not_found=False):
        return
    if env["website.page"].search_count([
            ("url", "=", URL_DEMO), ("website_id", "=", website.id)]):
        return
    arch = _ler_arch()
    pagina = env["website.page"].create({
        "name": "Cenas com scroll (demonstração)",
        "url": URL_DEMO,
        "website_id": website.id,
        "is_published": True,
        "website_indexed": False,
        "type": "qweb",
        "key": "website.pg_scroll_scenes_demo_%s" % website.id,
        "arch": arch,
    })
    env["ir.model.data"]._update_xmlids([{
        "xml_id": xmlid, "record": pagina, "noupdate": True}])


def post_init_criar_assets(env):
    website = _website_alvo(env)
    if not website:
        _logger.warning(
            "pg_website_scroll_scenes: não existe nenhum website com o nome pretendido; "
            "não se liga nada. Defina o parâmetro %s e reinstale.", PARAM_WEBSITE)
        return
    for sufixo, titulo, caminho, sequencia in ASSETS:
        _criar_asset(env, website, sufixo, titulo, caminho, sequencia)
    _criar_pagina_demo(env, website)
    _logger.info("pg_website_scroll_scenes: ligado ao website '%s' (id %s).",
                 website.name, website.id)
