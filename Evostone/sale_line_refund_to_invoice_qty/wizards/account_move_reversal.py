# Copyright 2021 ForgeFlow (http://www.forgeflow.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import api, fields, models


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    sale_qty_to_reinvoice = fields.Boolean(
        string="Esta nota de crédito será re-faturada",
        help="Deixe marcado se pretende re-faturar a mesma linha da ordem de venda "
        "(comportamento padrão)",
        readonly=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        company = (
            self.env["res.company"].browse(res.get("company_id"))
            if res.get("company_id")
            else self.env.company
        )
        res["sale_qty_to_reinvoice"] = company.reinvoice_credit_note_default
        return res

    def reverse_moves(self, is_modify=False):
        sale_qty_to_reinvoice = True if is_modify else self.sale_qty_to_reinvoice
        return super(
            AccountMoveReversal,
            self.with_context(sale_qty_to_reinvoice=sale_qty_to_reinvoice),
        ).reverse_moves(is_modify=is_modify)
