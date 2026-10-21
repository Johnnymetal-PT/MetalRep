# -*- coding: utf-8 -*-
"""A atualização para 19.0.1.1.0 apagou os assets do website (xmlids tratados como órfãos).

Recria-os e protege-os, e repõe a página. É seguro correr em bases onde os assets existem.
"""
from odoo import SUPERUSER_ID, api

from odoo.addons.pg_website_scroll_scenes.hooks import (
    atualizar_pagina_demo, garantir_assets)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    garantir_assets(env)
    atualizar_pagina_demo(env)
