# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    mh_map_cc_user_ids = fields.Many2many(
        related='company_id.mh_map_cc_user_ids',
        readonly=False,
        string='Cc dos Mapas (Cobranças/Pagamentos)',
    )
