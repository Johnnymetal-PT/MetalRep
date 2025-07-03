from odoo import models, fields, api

class ProductForbiddenUsers(models.Model):
    _name = 'product.forbidden.users'
    _description = 'List of Forbidden Users for Product Creation'
    _rec_name = 'email'

    email = fields.Char(string="Email", required=True, unique=True)

    def name_get(self):
        return [(record.id, record.email or "Unknown") for record in self]
