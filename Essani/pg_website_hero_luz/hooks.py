# -*- coding: utf-8 -*-
"""Liga a folha de estilos do Hero ao website escolhido, e só a esse.

Mesmo padrão do `pg_website_scroll_scenes`: o asset nasce com `website_id` preenchido (e não na
chave `assets` do manifesto, que o aplicaria a todos os websites da base). Se o website não
existir não se cria nada: um asset sem website valeria para todos.
"""

import logging

_logger = logging.getLogger(__name__)

PARAM_WEBSITE = "pg_website_hero_luz.website_name"
WEBSITE_POR_OMISSAO = "Essani V5"
MODULO = "pg_website_hero_luz"
SUFIXO_ASSET = "asset_css"
CAMINHO_CSS = "static/src/css/pg_hero_luz.css"


def _website_alvo(env):
    nome = env["ir.config_parameter"].sudo().get_param(
        PARAM_WEBSITE, WEBSITE_POR_OMISSAO)
    return env["website"].search([("name", "=", nome)], limit=1)


def garantir_asset(env):
    """Cria o asset se faltar e protege-o das atualizações. Seguro em bases onde já existe."""
    website = _website_alvo(env)
    if not website:
        return False
    xmlid = "%s.%s" % (MODULO, SUFIXO_ASSET)
    asset = env.ref(xmlid, raise_if_not_found=False)
    if not asset:
        asset = env["ir.asset"].create({
            "name": "%s: Hero, a luz acende (CSS)" % MODULO,
            "bundle": "web.assets_frontend",
            "directive": "append",
            "path": "%s/%s" % (MODULO, CAMINHO_CSS),
            # Depois do CSS das cenas (12) e do resto; o seletor usa `#wrap.pgh` e não depende
            # da ordem, mas assim fica claro que isto vem por cima.
            "sequence": 20,
            "website_id": website.id,
        })
    # `noupdate=True` e `update=True`: sem isto o Odoo trata o registo como órfão (não vem de
    # nenhum ficheiro de dados) e apaga-o ao atualizar o módulo. Ver o 19.0.1.2.0 das cenas.
    env["ir.model.data"]._update_xmlids([{
        "xml_id": xmlid, "record": asset, "noupdate": True}], update=True)
    return True


def post_init_ligar_ao_website(env):
    if not garantir_asset(env):
        _logger.warning(
            "pg_website_hero_luz: não existe nenhum website com o nome pretendido; "
            "não se liga nada. Defina o parâmetro %s e reinstale.", PARAM_WEBSITE)
        return
    _logger.info("pg_website_hero_luz: ligado ao website '%s'.",
                 _website_alvo(env).name)
