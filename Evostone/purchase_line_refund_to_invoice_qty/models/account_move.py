from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def copy(self, default=None):
        res = super().copy(default=default)
        purchase_qty_to_reinvoice = self.env.context.get(
            "purchase_qty_to_reinvoice", False
        )
        res.line_ids.write({"purchase_qty_to_reinvoice": purchase_qty_to_reinvoice})
        return res
