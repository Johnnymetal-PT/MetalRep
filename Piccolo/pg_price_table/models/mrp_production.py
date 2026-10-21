"""Aplicacao da tabela de consumo em mrp.production.

Override de ``create``:
1. Le ``price_N`` do template principal (N = product_qty).
2. Sobrescreve ``vals['product_uom_qty']`` com esse valor.
3. Para o componente raw "Tecido de Fornecedor" (match exato pelo
   nome), sobrescreve ``move.product_uom_qty`` com o mesmo valor
   tirado do **template principal**, nao do componente.

NOTA: este override coexiste com o de ``pg_tecidos``. A ordem do MRO
e ditada pela ordem em ``depends``. Validar manualmente caso o
comportamento seja inesperado.
"""
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.model
    def create(self, vals):
        product_variant = self.env['product.product'].browse(vals.get('product_id'))
        product_template = product_variant.product_tmpl_id if product_variant else None

        product_qty = vals.get('product_qty')

        # Consumo do template principal aplicado ao product_uom_qty
        # do proprio MO (a quantidade fabricada efetiva).
        consumption_value = self._get_consumption_value(product_template, product_qty)
        vals.update({'product_uom_qty': consumption_value})

        mo = super(MrpProduction, self).create(vals)

        # Procurar especificamente o componente chamado "Tecido de
        # Fornecedor" (match exato) - sobrescreve com o consumo do
        # template PRINCIPAL (nao do componente).
        for move in mo.move_raw_ids:
            if move.product_id.name == 'Tecido de Fornecedor':
                tecido_consumption_value = self._get_consumption_value(product_template, product_qty)
                move.product_uom_qty = tecido_consumption_value

        return mo

    def _get_consumption_value(self, product_template, product_qty):
        """Le price_1..price_10 do template e devolve a linha N.

        - qty <= 1 -> price_1
        - qty <= 2 -> price_2
        - ...
        - qty > 10 -> price_10
        """
        consumption_table = [
            product_template.price_1, product_template.price_2, product_template.price_3,
            product_template.price_4, product_template.price_5, product_template.price_6,
            product_template.price_7, product_template.price_8, product_template.price_9,
            product_template.price_10,
        ]

        # Match direto por quantidade. Cap superior em price_10.
        if product_qty <= 1:
            return consumption_table[0]
        elif product_qty <= 2:
            return consumption_table[1]
        elif product_qty <= 3:
            return consumption_table[2]
        elif product_qty <= 4:
            return consumption_table[3]
        elif product_qty <= 5:
            return consumption_table[4]
        elif product_qty <= 6:
            return consumption_table[5]
        elif product_qty <= 7:
            return consumption_table[6]
        elif product_qty <= 8:
            return consumption_table[7]
        elif product_qty <= 9:
            return consumption_table[8]
        elif product_qty <= 10:
            return consumption_table[9]
        else:
            return consumption_table[-1]
