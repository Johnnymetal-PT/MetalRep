# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    pg_transport_product_id = fields.Many2one(
        "product.product",
        string="Produto de Transporte",
        help="Produto usado nas linhas de venda para o custo de transporte. "
        "A calculadora aplica o valor calculado ao price_unit da linha "
        "deste produto.",
    )
    pg_transport_fuel_surcharge = fields.Float(
        string="Sobretaxa de Combustível (%)",
        default=0.0,
        help="Percentagem aplicada por defeito sobre o custo base. "
        "Editável em cada cálculo.",
    )
    pg_transport_client_margin = fields.Float(
        string="Margem Cliente (%)",
        default=25.0,
        help="Margem aplicada sobre o custo operacional (custo base + sobretaxa).",
    )
    pg_transport_pallet_fee = fields.Float(
        string="Valor por Palete (€)",
        default=15.0,
        help="Valor fixo somado por cada palete, após a margem.",
    )
