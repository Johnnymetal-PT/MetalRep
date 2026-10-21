from odoo import api, fields, models


class SaleOrderLinePriceCalculator(models.TransientModel):
    _name = "sale.order.line.price.calculator"
    _description = "Sale Order Line Price Calculator"

    sale_line_id = fields.Many2one("sale.order.line", required=True, readonly=True)
    cost_price = fields.Float(readonly=True, digits="Product Price")
    margin_type = fields.Selection(
        selection=[("fixed", "Fixed Amount"), ("percent", "Percentage")],
        default="fixed",
        required=True,
    )
    margin_value = fields.Float(digits="Product Price", required=True)
    margin_amount = fields.Float(compute="_compute_margin_amount", digits="Product Price")
    computed_price = fields.Float(compute="_compute_computed_price", digits="Product Price")
    observation = fields.Text()

    @api.depends("margin_type", "margin_value", "cost_price")
    def _compute_margin_amount(self):
        for wizard in self:
            if wizard.margin_type == "percent":
                wizard.margin_amount = wizard.cost_price * (wizard.margin_value or 0.0) / 100.0
            else:
                wizard.margin_amount = wizard.margin_value or 0.0

    @api.depends("margin_amount", "cost_price")
    def _compute_computed_price(self):
        for wizard in self:
            wizard.computed_price = (wizard.cost_price or 0.0) + (wizard.margin_amount or 0.0)

    def action_apply(self):
        self.ensure_one()
        line = self.sale_line_id
        if not line:
            return {"type": "ir.actions.act_window_close"}

        line.write(
            {
                "calculator_cost_price": self.cost_price,
                "calculator_margin_type": self.margin_type,
                "calculator_margin_value": self.margin_value,
                "calculator_margin_amount": self.margin_amount,
                "calculator_observation": self.observation,
                "price_unit": self.computed_price,
            }
        )
        return {"type": "ir.actions.act_window_close"}
