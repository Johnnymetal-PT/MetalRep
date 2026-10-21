# -*- coding: utf-8 -*-
"""Cria, só no website escolhido, a vista do rodapé e da newsletter, e aplica as traduções.

Mesmo padrão do `pg_website_scroll_scenes` e do `pg_website_hero_luz`: a vista nasce com
`website_id` preenchido (uma vista sem website valeria para todos, incluindo o site público).
Se o website não existir não se cria nada.
"""
import logging

from .vista import ARCH, LINGUAS, pedido

_logger = logging.getLogger(__name__)

PARAM_WEBSITE = "pg_website_footer_newsletter.website_name"
WEBSITE_POR_OMISSAO = "Essani V5"
MODULO = "pg_website_footer_newsletter"
NOME_XMLID = "vista_rodape"
CHAVE = "pg_website_footer_newsletter.rodape"


def _website_alvo(env):
    nome = env["ir.config_parameter"].sudo().get_param(PARAM_WEBSITE, WEBSITE_POR_OMISSAO)
    return env["website"].search([("name", "=", nome)], limit=1)


def aplicar_traducoes(view):
    """Escreve pt_PT e es_ES nos termos da vista (as línguas instaladas). Idempotente."""
    instaladas = {codigo for codigo, _ in view.env["res.lang"].get_installed()}
    linhas, _ctx = view.get_field_translations("arch_db")
    for lg, termos in pedido(linhas).items():
        if lg in instaladas and termos:
            view.update_field_translations("arch_db", {lg: termos})


def garantir_vista(env):
    """Cria a vista se faltar (protegida das atualizações) e aplica as traduções."""
    website = _website_alvo(env)
    if not website:
        return False
    xmlid = "%s.%s" % (MODULO, NOME_XMLID)
    view = env.ref(xmlid, raise_if_not_found=False)
    if not view:
        view = env["ir.ui.view"].create({
            "name": "PG Rodapé e Newsletter (%s)" % website.name,
            "type": "qweb",
            "inherit_id": env.ref("website.layout").id,
            "key": CHAVE,
            "website_id": website.id,
            "arch": ARCH,
            "active": True,
        })
    # `noupdate` + `update`: sem isto o Odoo trata o registo como órfão ao atualizar o módulo.
    env["ir.model.data"]._update_xmlids([{"xml_id": xmlid, "record": view, "noupdate": True}], update=True)
    aplicar_traducoes(view)
    return True


def post_init_criar_vista(env):
    if not garantir_vista(env):
        _logger.warning(
            "pg_website_footer_newsletter: não existe nenhum website com o nome pretendido; "
            "não se liga nada. Defina o parâmetro %s e reinstale.", PARAM_WEBSITE)
        return
    _logger.info("pg_website_footer_newsletter: vista criada para o website '%s'.",
                 _website_alvo(env).name)
