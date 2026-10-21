# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    mh_map_cc_user_ids = fields.Many2many(
        'res.users',
        'res_company_mh_map_cc_user_rel',
        'company_id', 'user_id',
        string='Cc dos Mapas (Cobranças/Pagamentos)',
        help='Utilizadores que entram em cópia (Cc) ao enviar por e-mail o '
             'Mapa de Cobranças (clientes) e o Mapa de Pagamentos (fornecedores).',
    )
