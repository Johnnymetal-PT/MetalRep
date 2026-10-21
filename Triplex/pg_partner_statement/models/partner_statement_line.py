"""
Definicao das linhas temporarias usadas pelo wizard de extrato simplificado de cliente.

Modulo: pg_partner_statement.
Ficheiro: pg_partner_statement\models\partner_statement_line.py.
Modelo principal: pg.partner.statement.line.
"""

from odoo import fields, models


class PartnerStatementLine(models.TransientModel):
    _name = "pg.partner.statement.line"
    _description = "Linha de Extrato Simplificado de Cliente"
    _order = "partner_name, currency_name"

    wizard_id = fields.Many2one(
        "pg.partner.statement.wizard",
        ondelete="cascade",
        required=True,
        index=True,
    )
    partner_id = fields.Many2one("res.partner", required=True, string="Cliente")
    partner_name = fields.Char(related="partner_id.name", store=True)
    currency_id = fields.Many2one("res.currency", required=True, string="Moeda")
    currency_name = fields.Char(related="currency_id.name", store=True)

    final_invoiced_amount = fields.Monetary(
        string="Faturas Finais",
        currency_field="currency_id",
        help="Soma das faturas de venda (excluindo adiantamentos) emitidas no período.",
    )
    downpayment_amount = fields.Monetary(
        string="Faturas de Adiantamento",
        currency_field="currency_id",
        help="Soma das faturas de adiantamento (down-payment) emitidas no período.",
    )
    refunded_amount = fields.Monetary(string="Notas de Crédito", currency_field="currency_id")
    net_invoiced_amount = fields.Monetary(string="Total Líquido", currency_field="currency_id")
    period_residual = fields.Monetary(
        string="Por Pagar do Período",
        currency_field="currency_id",
        help="Valor ainda em aberto das faturas emitidas no intervalo selecionado.",
    )
    total_balance = fields.Monetary(
        string="Saldo Total Conta Corrente",
        currency_field="currency_id",
        help="Saldo da conta corrente do cliente à data final do intervalo "
             "(inclui movimentos anteriores ao período).",
    )
