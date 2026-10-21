# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    # Editável mesmo com o pagamento lançado: a ligação é só informativa (não mexe no
    # lançamento) e permite associar adiantamentos registados antes deste módulo.
    pg_purchase_order_id = fields.Many2one(
        'purchase.order',
        string="Purchase Order",
        index='btree_not_null',
        copy=False,
        domain="[('partner_id', 'child_of', partner_id), ('company_id', '=', company_id),"
               " ('state', 'in', ('purchase', 'done'))]",
        help="Purchase order this vendor payment belongs to (advance or bill payment). "
             "The amount is shown on the purchase order as paid.",
    )
