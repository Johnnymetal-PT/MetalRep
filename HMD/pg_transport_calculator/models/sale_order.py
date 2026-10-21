# -*- coding: utf-8 -*-
"""Ponto de entrada da calculadora de transporte no orcamento.

Adiciona um botao no orcamento que abre o wizard de calculo/comparacao
de transporte. O wizard aplica o custo escolhido a linha de venda do
produto de transporte configurado (`res.company.pg_transport_product_id`).

Os inputs do calculo (pais, zona e embalagens) sao GUARDADOS no
orcamento (`pg_transport_*`), para que ao reabrir a calculadora apareca
o ultimo calculo em vez de ecra em branco.
"""

from odoo import _, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    pg_transport_line_id = fields.Many2one(
        "sale.order.line",
        compute="_compute_pg_transport_line_id",
        string="Linha de Transporte",
    )
    # Inputs persistidos da ultima utilizacao da calculadora de transporte
    pg_transport_country = fields.Char(string="Transporte: País")
    pg_transport_zone = fields.Char(string="Transporte: Zona")
    pg_transport_package_ids = fields.One2many(
        "pg.transport.order.package", "order_id", string="Embalagens de Transporte"
    )
    # Detalhe do custo que NAO entra no custo base (aba Logistics):
    # sobretaxa de combustivel e custo de paletes. Preenchido pela
    # calculadora ao aplicar; o custo base fica no campo Valor Orcamento.
    pg_transport_logistics_notes = fields.Text(
        string="Transporte: Observações Logística",
        help="Componentes do transporte que não entram no custo base "
             "(sobretaxa de combustível e custo de paletes). Preenchido "
             "automaticamente pela calculadora ao aplicar o custo.",
    )

    def _compute_pg_transport_line_id(self):
        for order in self:
            product = order.company_id.pg_transport_product_id
            line = self.env["sale.order.line"]
            if product:
                line = order.order_line.filtered(
                    lambda l: l.product_id == product and not l.display_type
                )[:1]
            order.pg_transport_line_id = line

    def action_open_transport_calculator(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Calculadora de Transporte"),
            "res_model": "pg.transport.calculator.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_order_id": self.id},
        }


class TransportOrderPackage(models.Model):
    _name = "pg.transport.order.package"
    _description = "Embalagem de transporte guardada no orçamento"
    _order = "order_id, sequence, id"

    order_id = fields.Many2one(
        "sale.order", required=True, ondelete="cascade", index=True
    )
    sequence = fields.Integer(default=10)
    package_type = fields.Selection(
        selection=[("box", "Caixa"), ("pallet", "Palete")],
        default="box",
        required=True,
        string="Tipo",
    )
    width = fields.Float(string="Largura (cm)")
    length = fields.Float(string="Comprimento (cm)")
    height = fields.Float(string="Altura (cm)")
    quantity = fields.Float(string="Qtd", default=1.0)
