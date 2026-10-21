from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    phc_customer_number = fields.Char(
        string="N.º Cliente PHC",
        index="btree_not_null",
        copy=False,
        help="Número do cliente no PHC (NR_CLIENTE). Serve para cruzar o histórico com o PHC.",
    )
    phc_history_amount = fields.Monetary(
        string="Volume Histórico PHC",
        currency_field="currency_id",
        copy=False,
        help="Faturação acumulada do cliente no PHC até à data de corte de 31/12/2025. "
             "A faturação a partir de 01/01/2026 está nas faturas do Odoo.",
    )
