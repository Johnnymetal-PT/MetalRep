from odoo import models, fields


class AccountAccount(models.Model):
    _inherit = 'account.account'

    is_orphan = fields.Boolean(
        string='Conta Órfã',
        default=False,
        help='Conta importada do sistema antigo sem parceiro associado. Excluída da sequência automática.',
    )
