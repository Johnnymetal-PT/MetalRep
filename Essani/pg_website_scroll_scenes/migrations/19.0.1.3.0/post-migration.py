# -*- coding: utf-8 -*-
"""Repõe a página com o novo acabamento das cenas e garante os assets do website.

É seguro correr em bases onde os assets já existem.
"""
from odoo import SUPERUSER_ID, api

from odoo.addons.pg_website_scroll_scenes.hooks import (
    atualizar_pagina_demo, garantir_assets)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    garantir_assets(env)
    atualizar_pagina_demo(env)
