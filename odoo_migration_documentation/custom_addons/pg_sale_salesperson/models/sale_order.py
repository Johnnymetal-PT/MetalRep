"""Campo de salesperson (parceiro) nas encomendas de venda.

Complementa o user_id standard com um contacto comercial especifico para
segmentacao, reporting e navegacao cruzada com parceiros.
"""

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Campo paralelo ao user_id standard para representar "comercial contacto"
    # quando a atribuicao comercial nao coincide com o utilizador interno.
    salesperson_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Salesperson",
        help="Salesperson contact associated with the order.",
    )
