from odoo import models, fields

class ResCompany(models.Model):
    _inherit = "res.company"

    jas_company = fields.Char(string="Empresa")
    jas_username = fields.Char(string="Utilizador")
    jas_password = fields.Char(string="Autorização")
    jas_tenant_key = fields.Char(string="Chave (xxxxxx)")
    jas_org_key = fields.Char(string="Chave organização (xxxxxx-xxxx)")
    jas_ft = fields.Char(string="Fatura")
    jas_fr = fields.Char(string="Fatura recibo")
    jas_fs = fields.Char(string="Fatura simplificada")

