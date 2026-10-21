"""Override de `product.template.create` para bloquear utilizadores na blocklist.

Pertence ao modulo `pg_restrict_product_creation`. A mensagem da UserError
mantem o texto original apesar de aparentar copy/paste (deveria dizer "nao
tem permissao para criar produtos"). Ver FAQ no `__manifest__.py`.
"""
from odoo import models, api
from odoo.exceptions import UserError

class RestrictProductCreation(models.Model):
    """Extensao de `product.template` que valida a blocklist em `create`."""

    _inherit = 'product.template'

    @api.model
    def create(self, vals):
        """Bloqueia criacao de produtos para utilizadores na blocklist."""
        user_email = self.env.user.login
        forbidden_users = self.env['product.forbidden.users'].search([('email', '=', user_email)])

        if forbidden_users:
            # Texto da mensagem aparenta copy/paste; a acao bloqueada e
            # criar produto, nao mexer na lista.
            raise UserError("Não pode alterar a lista de utilizadores bloqueados.")

        return super().create(vals)

