# -*- coding: utf-8 -*-
"""A página de demonstração passou a ter a homepage inteira em cenas; repõe-na na base."""
from odoo import SUPERUSER_ID, api

from odoo.addons.pg_website_scroll_scenes.hooks import atualizar_pagina_demo


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    atualizar_pagina_demo(env)
