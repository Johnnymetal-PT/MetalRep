# -*- coding: utf-8 -*-
"""Ponte entre a simulacao de transporte do orcamento e a entrega.

Nivel 1 (reutilizacao/informativo): ao criar a entrega ao cliente a
partir de uma venda que tem embalagens simuladas na calculadora de
transporte (``sale.order.pg_transport_package_ids``), copiamos essas
embalagens para uma lista editavel na entrega
(``stock.picking.pg_transport_package_ids``).

Objetivo: a informacao definida na simulacao (caixas/paletes e
dimensoes) fica registada e disponivel na preparacao da expedicao,
podendo ser ajustada, em vez de ser reintroduzida.

Esta camada NAO cria embalagens standard (``stock.quant.package``) nem
interfere com o fluxo "Put in Pack"; e uma copia snapshot, editavel.
"""

from odoo import _, api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    pg_transport_package_ids = fields.One2many(
        "pg.transport.picking.package",
        "picking_id",
        string="Embalagens Previstas",
        help="Embalagens (caixas/paletes) definidas na simulacao de "
             "transporte do orcamento. Copiadas ao criar a entrega e "
             "editaveis na preparacao da expedicao.",
    )
    pg_transport_package_count = fields.Integer(
        compute="_compute_pg_transport_package_count",
    )

    @api.depends("pg_transport_package_ids")
    def _compute_pg_transport_package_count(self):
        for picking in self:
            picking.pg_transport_package_count = len(picking.pg_transport_package_ids)

    def _pg_copy_transport_packages(self):
        """Copia as embalagens do orcamento de origem para a entrega.

        So actua em entregas ao cliente (``outgoing``) ligadas a uma
        venda com embalagens simuladas. Nao duplica se ja existirem
        embalagens previstas na entrega.
        """
        for picking in self:
            order = picking.sale_id
            if not order or not order.pg_transport_package_ids:
                continue
            if picking.picking_type_id.code != "outgoing":
                continue
            if picking.pg_transport_package_ids:
                continue
            picking.pg_transport_package_ids = [
                (0, 0, {
                    "sequence": p.sequence,
                    "package_type": p.package_type,
                    "width": p.width,
                    "length": p.length,
                    "height": p.height,
                    "quantity": p.quantity,
                })
                for p in order.pg_transport_package_ids
            ]

    @api.model_create_multi
    def create(self, vals_list):
        pickings = super().create(vals_list)
        pickings._pg_copy_transport_packages()
        return pickings

    def action_pg_copy_transport_packages(self):
        """Botao: repor as embalagens previstas a partir do orcamento.

        Substitui a lista atual pela do orcamento (util se foi apagada
        ou se o orcamento foi recalculado depois da entrega criada).
        """
        self.ensure_one()
        order = self.sale_id
        if not order or not order.pg_transport_package_ids:
            return
        self.pg_transport_package_ids.unlink()
        self._pg_copy_transport_packages()


class TransportPickingPackage(models.Model):
    _name = "pg.transport.picking.package"
    _description = "Embalagem prevista na entrega (do orcamento)"
    _order = "picking_id, sequence, id"

    picking_id = fields.Many2one(
        "stock.picking", required=True, ondelete="cascade", index=True
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
