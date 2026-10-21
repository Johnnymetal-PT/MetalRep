from odoo import fields, models
from odoo.exceptions import UserError


class StickerPrintWizard(models.TransientModel):
    _name = 'sticker.print.wizard'
    _description = 'Wizard de Impressão de Stickers'

    picking_id = fields.Many2one(
        'stock.picking',
        string='Picking',
        required=True,
        readonly=True,
    )

    print_type = fields.Selection([
        ('zpl', 'ZPL (Zebra)'),
        ('pdf', 'PDF (A4)'),
    ], string='Tipo de Impressão', required=True, default='zpl')

    def action_print(self):
        self.ensure_one()
        picking = self.picking_id

        move_lines = picking.move_line_ids.filtered(
            lambda ml: ml.lot_id and ml.lot_id.sudo().price_group_id
        )

        if not move_lines:
            raise UserError(
                "Não há linhas com lotes válidos para imprimir stickers.\n\n"
                "Verifique se:\n"
                "- As linhas têm lotes atribuídos\n"
                "- Os lotes têm grupo de preço definido"
            )

        move_lines = move_lines.sorted(key=lambda ml: ml.lot_id.code or '')

        if self.print_type == 'pdf':
            return self.env.ref(
                'mh_stone_reports.action_report_stickers'
            ).report_action(move_lines)
        else:
            return self.env.ref(
                'mh_stone_reports.action_report_stickers_zpl'
            ).report_action(move_lines)
