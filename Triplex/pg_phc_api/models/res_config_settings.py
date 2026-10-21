# -*- coding: utf-8 -*-
"""
Campos de parametrizacao do conector PHC ao nivel da empresa e das Definicoes.

Modulo: pg_phc_api.
Ficheiro: pg_phc_api\models\res_config_settings.py.
Modelos principais: res.company e res.config.settings.
"""

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    phc_api_base_url = fields.Char(
        string="PHC WS URL",
        help="Endpoint SOAP PHC CSWeb, ex: https://erp.parametro.pt:8443/DEVphcodoo/ws/wscript.asmx",
    )
    phc_api_user = fields.Char(
        string="Utilizador PHC",
        help="Username para autenticacao no PHC.",
    )
    phc_api_password = fields.Char(
        string="Password PHC",
        help="Password para autenticacao no PHC.",
    )


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    phc_api_base_url = fields.Char(
        related="company_id.phc_api_base_url",
        readonly=False,
        string="PHC WS URL",
    )
    phc_api_user = fields.Char(
        related="company_id.phc_api_user",
        readonly=False,
        string="Utilizador PHC",
    )
    phc_api_password = fields.Char(
        related="company_id.phc_api_password",
        readonly=False,
        string="Password PHC",
    )
