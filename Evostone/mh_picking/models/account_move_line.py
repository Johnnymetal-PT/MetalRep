# Copyright 2025 MH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    lot_id = fields.Many2one(
        'stock.lot',
        string='SN',
        copy=True,
        help='Número de série associado a esta linha da fatura'
    )

    lot_name = fields.Char(
        string='Lote',
        copy=True,
        help='Lote associado a esta linha da fatura'
    )

    # Campos de dimensão (copiados do sale.order.line/purchase.order.line)
    units_qty = fields.Integer(
        string='Quantidade',
        copy=True,
        help='Número de peças/unidades'
    )

    length = fields.Float(
        string='Comprimento',
        digits='Dimensions',
        copy=True,
        help='Comprimento em metros'
    )

    width = fields.Float(
        string='Largura',
        digits='Dimensions',
        copy=True,
        help='Largura em metros'
    )

    thickness = fields.Float(
        string='Espessura',
        digits='Dimensions',
        copy=True,
        help='Espessura em metros'
    )

    peso = fields.Float(
        string='Peso',
        digits='Dimensions',
        copy=True,
        help='Peso em kg'
    )

    # Campos de controlo para readonly (como sale.order.line)
    units_qty_editable = fields.Boolean(
        string='Quantidade Editável',
        compute='_compute_editability',
        help='Indica se units_qty pode ser editado (True para produtos sem forma física)'
    )

    thickness_editable = fields.Boolean(
        string='Espessura Editável',
        compute='_compute_editability',
        help='Indica se thickness pode ser editado (True para blocos)'
    )

    lot_required = fields.Boolean(
        string='Lote Obrigatório',
        compute='_compute_editability',
        help='Indica se lot_id é obrigatório (True para produtos com tracking)'
    )

    @api.depends('product_id', 'product_id.product_form', 'product_id.tracking', 'sale_line_ids')
    def _compute_editability(self):
        """
        Calcula se os campos são editáveis baseado no tipo de produto.

        - units_qty_editable: True se product_form == 'none' (produtos normais)
        - thickness_editable: True se product_form == 'block' (blocos)
        - lot_required: True se product.tracking != 'none' E vem de uma venda
        """
        for line in self:
            product = line.product_id
            if product:
                product_form = product.product_form
                line.units_qty_editable = product_form == 'none'
                line.thickness_editable = product_form == 'block'
                # Lote obrigatório apenas se tem tracking E vem de uma venda
                is_from_sale = bool(line.sale_line_ids)
                line.lot_required = product.tracking != 'none' and is_from_sale
            else:
                line.units_qty_editable = True
                line.thickness_editable = False
                line.lot_required = False
