from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    pg_early_discount_eligible = fields.Boolean(
        string="Aplicar desconto P.P.",
        default=True,
        copy=True,
        help=(
            "Quando ativo, esta linha é incluída na base de cálculo do desconto "
            "de pronto pagamento definido no termo de pagamento da fatura."
        ),
    )
