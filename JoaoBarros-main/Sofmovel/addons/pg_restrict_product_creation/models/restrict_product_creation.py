from odoo import models, api
from odoo.exceptions import UserError

class RestrictProductCreation(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals):
        """Block product creation for forbidden users."""
        user_email = self.env.user.login
        forbidden_users = self.env['product.forbidden.users'].search([('email', '=', user_email)])

        if forbidden_users:
            raise UserError("Não pode alterar a lista de utilizadores bloqueados.")

        return super().create(vals)

