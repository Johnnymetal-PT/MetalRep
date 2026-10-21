# -*- coding: utf-8 -*-
"""Wizard `sale.order.line.components.calculator`.

Calculadora de preco de produto por componentes, replicando o
`CALCULO PRECOS.xlsx` da HMD:

  PC TOTAL      = PC1 + PC2 + PC3 + PC4
  PRECO CLIENTE = (CAIXA + PC_TOTAL) / 0,6 + P.RECOLHA
  PVP           = PRECO CLIENTE * 2
  FATURADO      = PVP * 0,6            (= PRECO CLIENTE * 1,2)
  MARGEM REAL   = (FATURADO + PC_TOTAL) / FATURADO

Ao confirmar, guarda os inputs/outputs na `sale.order.line` (para
rastreabilidade) e escreve o valor escolhido em `price_unit`.

Complementa o wizard de custo+margem (`sale.order.line.price.calculator`),
que se mantem como fallback.
"""

from odoo import api, fields, models


class SaleOrderLineComponentsCalculator(models.TransientModel):
    _name = "sale.order.line.components.calculator"
    _description = "Sale Order Line Components Price Calculator"

    sale_line_id = fields.Many2one("sale.order.line", required=True, readonly=True)

    pc1 = fields.Float(string="PC1", digits="Product Price")
    forn1 = fields.Char(string="Fornecedor 1")
    pc2 = fields.Float(string="PC2", digits="Product Price")
    forn2 = fields.Char(string="Fornecedor 2")
    pc3 = fields.Float(string="PC3", digits="Product Price")
    forn3 = fields.Char(string="Fornecedor 3")
    pc4 = fields.Float(string="PC4", digits="Product Price")
    forn4 = fields.Char(string="Fornecedor 4")
    box_cost = fields.Float(string="Caixa", digits="Product Price")
    pickup_cost = fields.Float(string="P. Recolha", digits="Product Price")

    pc_total = fields.Float(compute="_compute_values", digits="Product Price")
    price_client = fields.Float(
        string="Preço Cliente", compute="_compute_values", digits="Product Price"
    )
    pvp = fields.Float(string="PVP", compute="_compute_values", digits="Product Price")
    invoiced = fields.Float(
        string="Preço Faturado", compute="_compute_values", digits="Product Price"
    )
    margin_real = fields.Float(string="Margem Real", compute="_compute_values")

    apply_target = fields.Selection(
        selection=[
            ("pvp", "PVP"),
            ("pvp_disc40", "PVP com -40% (= Faturado)"),
            ("invoiced", "Preço Faturado"),
            ("client", "Preço Cliente"),
        ],
        string="Aplicar à linha",
        default="pvp",
        required=True,
        help="Valor a escrever no preço unitário da linha. 'PVP com -40%' "
        "aplica o PVP e um desconto de 40% (subtotal = Preço Faturado).",
    )
    observation = fields.Text(string="Observações")

    @api.depends("pc1", "pc2", "pc3", "pc4", "box_cost", "pickup_cost")
    def _compute_values(self):
        for wiz in self:
            pc_total = (
                (wiz.pc1 or 0.0) + (wiz.pc2 or 0.0)
                + (wiz.pc3 or 0.0) + (wiz.pc4 or 0.0)
            )
            client = ((wiz.box_cost or 0.0) + pc_total) / 0.6 + (wiz.pickup_cost or 0.0)
            pvp = client * 2.0
            invoiced = pvp * 0.6
            wiz.pc_total = pc_total
            wiz.price_client = client
            wiz.pvp = pvp
            wiz.invoiced = invoiced
            wiz.margin_real = (invoiced + pc_total) / invoiced if invoiced else 0.0

    def action_apply(self):
        self.ensure_one()
        line = self.sale_line_id
        if not line:
            return {"type": "ir.actions.act_window_close"}

        price_map = {
            "pvp": self.pvp,
            "pvp_disc40": self.pvp,
            "invoiced": self.invoiced,
            "client": self.price_client,
        }
        vals = {
            "calc_pc1": self.pc1,
            "calc_forn1": self.forn1,
            "calc_pc2": self.pc2,
            "calc_forn2": self.forn2,
            "calc_pc3": self.pc3,
            "calc_forn3": self.forn3,
            "calc_pc4": self.pc4,
            "calc_forn4": self.forn4,
            "calc_box_cost": self.box_cost,
            "calc_pickup_cost": self.pickup_cost,
            "price_unit": price_map[self.apply_target],
        }
        if self.observation:
            vals["calculator_observation"] = self.observation
        if self.apply_target == "pvp_disc40":
            vals["discount"] = 40.0
        line.write(vals)
        return {"type": "ir.actions.act_window_close"}
