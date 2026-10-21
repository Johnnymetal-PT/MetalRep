from odoo import _, api, fields, models


class MrpProductionZeroQtyWarning(models.TransientModel):
    _name = 'mrp.production.zero.qty.warning'
    _description = 'Zero Quantity Component Warning'

    production_ids = fields.Many2many('mrp.production', string='Manufacturing Orders')
    zero_component_message = fields.Text(string='Components', readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        production_ids = self.env.context.get('default_production_ids', [])
        productions = self.env['mrp.production'].browse(production_ids)
        res['production_ids'] = [(6, 0, productions.ids)]

        message = self.env.context.get('default_zero_component_message')
        if not message and productions:
            zero_moves = productions._get_zero_quantity_components()
            message = productions._format_zero_qty_message(zero_moves)
        res['zero_component_message'] = message
        return res

    def action_confirm_mo(self):
        self.ensure_one()
        productions = self.production_ids.with_context(skip_zero_qty_warning=True)
        productions.action_confirm()
        return {'type': 'ir.actions.act_window_close'}

    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}
