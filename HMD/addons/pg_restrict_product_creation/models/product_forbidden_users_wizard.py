from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProductForbiddenUsersWizard(models.TransientModel):
    _name = 'product.forbidden.users.wizard'
    _description = 'Manage Forbidden Users'

    forbidden_users_ids = fields.Many2many('product.forbidden.users', string="Utilizadores Bloqueados")

    @api.model
    def default_get(self, fields):
        """Pre-load existing forbidden users."""
        res = super().default_get(fields)
        existing_users = self.env['product.forbidden.users'].search([])
        res['forbidden_users_ids'] = [(6, 0, existing_users.ids)]
        return res

    def action_save(self):
        """Save the selected forbidden users."""
        # Get current forbidden emails
        current_forbidden_users = self.env['product.forbidden.users'].search([])
        selected_forbidden_users = self.forbidden_users_ids

        # Remove users that are no longer in the selection
        for user in current_forbidden_users:
            if user not in selected_forbidden_users:
                user.unlink()

        # Add new forbidden users
        for user in selected_forbidden_users:
            if not current_forbidden_users.filtered(lambda u: u.email == user.email):
                self.env['product.forbidden.users'].create({'email': user.email})

        return {'type': 'ir.actions.act_window_close'}

