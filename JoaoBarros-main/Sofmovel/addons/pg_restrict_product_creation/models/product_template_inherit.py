from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    # List of authorized emails
    ALLOWED_USERS = [
        "it.odoo@parametro.pt",
        "andreiasilva@sofmovel.pt",
        "gabrielpereira@sofmovel.pt",
        "pessoal@sofmovel.pt",
        "joaosilva@sofmovel.pt",
    ]

    show_forbidden_users_button = fields.Boolean(
        compute='_compute_show_button',
        store=False
    )

    @api.depends_context('uid')
    def _compute_show_button(self):
        """Ensure only allowed users see the button."""
        current_user_email = self.env.user.login  # Get the logged-in user's email
        for record in self:
            record.show_forbidden_users_button = current_user_email in self.ALLOWED_USERS

    def action_manage_forbidden_users(self):
        """Restrict access to the button action."""
        if self.env.user.login not in self.ALLOWED_USERS:
            raise UserError(_("You are not authorized to manage forbidden users."))

        return {
            'name': _('Manage Forbidden Users'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.forbidden.users.wizard',
            'view_mode': 'form',
            'target': 'new',
        }

class ProductTemplateInherit(models.Model):
    _inherit = 'product.product'

    # List of authorized emails
    ALLOWED_USERS = [
        "it.odoo@parametro.pt",
        "andreiasilva@sofmovel.pt",
        "gabrielpereira@sofmovel.pt",
        "pessoal@sofmovel.pt",
        "joaosilva@sofmovel.pt",
    ]

    show_forbidden_users_button = fields.Boolean(
        compute='_compute_show_button',
        store=False
    )

    @api.depends_context('uid')
    def _compute_show_button(self):
        """Ensure only allowed users see the button."""
        current_user_email = self.env.user.login  # Get the logged-in user's email
        for record in self:
            record.show_forbidden_users_button = current_user_email in self.ALLOWED_USERS

    def action_manage_forbidden_users(self):
        """Restrict access to the button action."""
        if self.env.user.login not in self.ALLOWED_USERS:
            raise UserError(_("You are not authorized to manage forbidden users."))

        return {
            'name': _('Manage Forbidden Users'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.forbidden.users.wizard',
            'view_mode': 'form',
            'target': 'new',
        }


