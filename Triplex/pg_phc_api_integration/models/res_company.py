# -*- coding: utf-8 -*-
"""
Campos de empresa usados pela integracao PHC para configuracao e controlo do envio.

Modulo: pg_phc_api_integration.
Ficheiro: pg_phc_api_integration/models/res_company.py.
Modelo principal: res.company.
"""


from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    # Credenciais legadas mantidas neste módulo para retrocompatibilidade.
    # O fluxo atual de envio usa os campos `phc_api_*` do módulo pg_phc_api.
    phc_username = fields.Char(string="Username")
    phc_password = fields.Char(string="Password")
