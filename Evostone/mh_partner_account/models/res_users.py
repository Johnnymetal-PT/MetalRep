# -*- coding: utf-8 -*-

from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    ask_create_partner_account = fields.Boolean(
        string='Perguntar Antes de Criar Conta',
        default=True,
        help='Se ativo, pergunta ao utilizador se deseja criar conta contabilística '
             'ao criar um novo parceiro. Se inativo, cria automaticamente sem perguntar.'
    )
