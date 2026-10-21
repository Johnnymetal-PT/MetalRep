# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError

CONSUMPTION_CLASSIFICATIONS = ('fixed_asset',)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    consumption_id = fields.Many2one(
        'internal.consumption',
        string='Consumo Interno',
        readonly=True,
        copy=False,
    )
    material_consumption_id = fields.Many2one(
        'material.consumption',
        string='Consumo de Material',
        readonly=True,
        copy=False,
    )

    def button_validate(self):
        """Bloquear validação se artigos de consumo não tiverem a localização de consumo."""
        for picking in self:
            if picking.picking_type_code not in ('incoming', 'internal'):
                continue

            # Pickings gerados pelos docs de consumo não são validados aqui
            if picking.consumption_id or picking.material_consumption_id:
                continue

            # Retornos (devoluções) vão para stock, não para consumo
            if picking.return_id:
                continue

            consumption_loc = self.env['stock.location'].search([
                ('usage', '=', 'internal'),
                ('is_consumption', '=', True),
                ('company_id', '=', picking.company_id.id),
            ], limit=1)
            if not consumption_loc:
                continue

            # Artigos de consumo devem ir para a localização de consumo
            bad_lines = picking.move_line_ids.filtered(
                lambda ml: (
                    ml.product_id.product_classification in CONSUMPTION_CLASSIFICATIONS
                    and ml.location_dest_id != consumption_loc
                )
            )
            if bad_lines:
                products = ', '.join(bad_lines.mapped('product_id.display_name'))
                raise UserError(_(
                    'Os seguintes artigos devem ter a localização de destino "%s":\n\n%s',
                    consumption_loc.display_name,
                    products,
                ))

            # Artigos que NÃO são de consumo não podem ir para a localização de consumo
            wrong_lines = picking.move_line_ids.filtered(
                lambda ml: (
                    ml.product_id.product_classification not in CONSUMPTION_CLASSIFICATIONS
                    and ml.location_dest_id == consumption_loc
                )
            )
            if wrong_lines:
                products = ', '.join(wrong_lines.mapped('product_id.display_name'))
                raise UserError(_(
                    'Os seguintes artigos não podem ter a localização de destino "%s".\n'
                    'Apenas artigos de classificação Imobilizado/Consumivel '
                    'podem ser recepcionados nessa localização:\n\n%s',
                    consumption_loc.display_name,
                    products,
                ))

        res = super().button_validate()

        # Se o picking tem consumption_id/material_consumption_id e foi validado, concluir o doc
        for picking in self:
            if picking.consumption_id and picking.state == 'done':
                if picking.consumption_id.state == 'confirmed':
                    picking.consumption_id.state = 'done'
            if picking.material_consumption_id and picking.state == 'done':
                if picking.material_consumption_id.state == 'confirmed':
                    picking.material_consumption_id.state = 'done'

        return res

    def action_cancel(self):
        """Se o picking tem consumption_id, cancelar o doc de consumo associado."""
        res = super().action_cancel()

        for picking in self:
            if picking.consumption_id and picking.consumption_id.state not in ('done', 'cancelled'):
                picking.consumption_id.state = 'cancelled'
            if picking.material_consumption_id and picking.material_consumption_id.state not in ('done', 'cancelled'):
                picking.material_consumption_id.state = 'cancelled'

        return res
