from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class ResPartner(models.Model):
    _inherit = "res.partner"

    salesperson_id = fields.Many2one(
        comodel_name="res.partner",
        string="Salesperson",
        help="Salesperson responsible for this contact.",
    )

    salesperson_order_count = fields.Integer(
        string="Sales Orders as Salesperson",
        compute="_compute_salesperson_order_count",
    )

    @api.depends()
    def _compute_salesperson_order_count(self):
        sale_order = self.env["sale.order"]
        for partner in self:
            partner.salesperson_order_count = sale_order.search_count(
                [("salesperson_partner_id", "=", partner.id)]
            )

    def action_view_salesperson_orders(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("sale.action_orders")
        action["domain"] = [
            ("salesperson_partner_id", "=", self.id),
        ]
        context = action.get("context") or {}
        if isinstance(context, str):
            context = safe_eval(context)
        context.update({"default_salesperson_partner_id": self.id})
        action["context"] = context
        return action
