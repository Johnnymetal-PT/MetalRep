# -*- coding: utf-8 -*-
"""Código HS (commodity code) ao nível da linha da fatura.

O Odoo standard guarda o código HS (commodity code) apenas no produto
(`product.product.intrastat_code_id`). A declaração Intrastat oficial lê-o
do produto (ver `account_intrastat/models/account_intrastat_report.py`).

Em HMD a maioria dos produtos não tem código HS preenchido (poucos
produtos têm) e há necessidade de o indicar/corrigir por linha de fatura,
à semelhança do que já existe para `intrastat_transaction_id` (Intrastat)
e `intrastat_product_origin_country_id` (País do Produto).

Este campo segue o mesmo padrão dos campos Intrastat standard da linha:
- `compute` a partir do produto (default sensato),
- `store=True, readonly=False` → herda do produto mas é editável/sobrepon-
  ível por linha.
"""

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    pg_intrastat_code_id = fields.Many2one(
        comodel_name="account.intrastat.code",
        string="Código HS",
        compute="_compute_pg_intrastat_code_id",
        store=True,
        readonly=False,
        domain="[('type', '=', 'commodity')]",
        help="Código HS (commodity code) desta linha. Por defeito herda o "
             "código HS do produto, mas pode ser definido/corrigido por linha.",
    )

    @api.depends("product_id")
    def _compute_pg_intrastat_code_id(self):
        for line in self:
            line.pg_intrastat_code_id = line.product_id.intrastat_code_id
