# -*- coding: utf-8 -*-
"""Diário por defeito de faturas de fornecedor, configurável por empresa."""

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    pg_default_purchase_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Diário por defeito de faturas de fornecedor",
        domain="[('type', '=', 'purchase'), ('company_id', '=', id)]",
        help="Diário pré-selecionado ao criar faturas e notas de crédito de "
             "fornecedor (incluindo a partir de pedidos de compra).\n"
             "- Vazio: mantém-se o comportamento standard do Odoo (diário de "
             "compra com sequência mais baixa que o utilizador consegue ver).\n"
             "- Preenchido: este diário passa a ser o default.\n"
             "A escolha manual do utilizador no formulário é sempre respeitada.",
    )
