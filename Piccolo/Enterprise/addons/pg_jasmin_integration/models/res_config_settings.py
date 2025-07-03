# -*- coding: utf-8 -*-

from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    jas_company = fields.Char(related="company_id.jas_company", readonly=False, string="Empresa")
    jas_username = fields.Char(related="company_id.jas_username", readonly=False, string="Utilizador")
    jas_password = fields.Char(related="company_id.jas_password", readonly=False, string="Autorização")
    jas_tenant_key = fields.Char(related="company_id.jas_tenant_key", readonly=False, string="Chave (xxxxxx)")
    jas_org_key = fields.Char(related="company_id.jas_org_key", readonly=False, string="Chave organização (xxxxxx-xxxx)")
    jas_ft = fields.Char(related="company_id.jas_ft", readonly=False, string="Fatura", config_parameter='pg_jasmin_integration.jas_ft')
    jas_fr = fields.Char(related="company_id.jas_fr", readonly=False, string="Fatura recibo")
    jas_fs = fields.Char(related="company_id.jas_fs", readonly=False, string="Fatura simplificada")
    
