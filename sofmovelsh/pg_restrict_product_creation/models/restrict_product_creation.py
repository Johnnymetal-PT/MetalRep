"""Override de `product.template.create` para bloquear utilizadores na blocklist.

Pertence ao modulo `pg_restrict_product_creation`. Port V17->V19: `create`
passou a `@api.model_create_multi` (assinatura obrigatória em v18+) e a
mensagem de erro foi corrigida (o texto original era copy/paste).
"""
from odoo import models, api, _
from odoo.exceptions import UserError


class RestrictProductCreation(models.Model):
    """Extensao de `product.template` que valida a blocklist em `create`."""

    _inherit = 'product.template'

    @api.model_create_multi
    def create(self, vals_list):
        """Bloqueia criacao de produtos para utilizadores na blocklist."""
        user_email = self.env.user.login
        forbidden = self.env['product.forbidden.users'].sudo().search_count(
            [('email', '=', user_email)]
        )
        if forbidden:
            raise UserError(_("Não tem permissão para criar produtos."))
        return super().create(vals_list)
