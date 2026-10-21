from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    prestashop_customer_id = fields.Char(
        string="Prestashop Customer ID",
        copy=False,
        index=True,
    )
    prestashop_shop_id = fields.Char(
        string="Prestashop Shop ID",
        copy=False,
        index=True,
    )
    prestashop_content_id = fields.Char(
        string="Prestashop Content ID",
        copy=False,
        index=True,
        help="CloudSync record identifier for this customer.",
    )
