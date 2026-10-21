# -*- coding: utf-8 -*-
"""
Campos de configuracao da integracao PHC ao nivel de empresa (versao legacy).

Modulo: pg_phc_api_integration_old.
Ficheiro: pg_phc_api_integration_old\models\res_company.py.
Modelo principal: res.company.
"""


from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    phc_username = fields.Char(string="Username")
    phc_password = fields.Char(string="Password")
