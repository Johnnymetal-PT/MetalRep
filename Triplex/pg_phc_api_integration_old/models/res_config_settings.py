# -*- coding: utf-8 -*-
"""
Ponte de Definicoes para editar parametros de integracao PHC guardados em res.company (legacy).

Modulo: pg_phc_api_integration_old.
Ficheiro: pg_phc_api_integration_old\models\res_config_settings.py.
Modelo principal: res.config.settings.
"""


from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    phc_username = fields.Char(
        related="company_id.phc_username", readonly=False, string="Username")
    phc_password = fields.Char(
        related="company_id.phc_password", readonly=False, string="Password")
