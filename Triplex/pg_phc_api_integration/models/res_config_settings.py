# -*- coding: utf-8 -*-
"""
Exposicao, em Definicoes, dos parametros de empresa usados na integracao PHC.

Modulo: pg_phc_api_integration.
Ficheiro: pg_phc_api_integration/models/res_config_settings.py.
Modelo principal: res.config.settings (proxy de res.company).
"""


from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Campos relacionados para editar credenciais diretamente em Definições;
    # a persistência real fica em `res.company`.
    phc_username = fields.Char(
        related="company_id.phc_username", readonly=False, string="Username")
    phc_password = fields.Char(
        related="company_id.phc_password", readonly=False, string="Password")
