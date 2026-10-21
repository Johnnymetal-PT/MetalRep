# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pg_transport_product_id = fields.Many2one(
        related="company_id.pg_transport_product_id",
        string="Produto de Transporte",
        readonly=False,
    )
    pg_transport_fuel_surcharge = fields.Float(
        related="company_id.pg_transport_fuel_surcharge", readonly=False,
    )
    pg_transport_client_margin = fields.Float(
        related="company_id.pg_transport_client_margin", readonly=False,
    )
    pg_transport_pallet_fee = fields.Float(
        related="company_id.pg_transport_pallet_fee", readonly=False,
    )
