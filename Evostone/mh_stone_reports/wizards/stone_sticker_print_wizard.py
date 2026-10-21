from odoo import api, fields, models


class StoneStickerPrintWizard(models.TransientModel):
    _name = 'stone.sticker.print.wizard'
    _description = 'Wizard de Impressão de Stickers (Stone Stock)'

    stone_stock_ids = fields.Many2many(
        'stone.stock',
        string='Placas',
        readonly=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('active_model') == 'stone.stock' and self.env.context.get('active_ids'):
            res['stone_stock_ids'] = [(6, 0, self.env.context['active_ids'])]
        return res

    print_type = fields.Selection([
        ('zpl', 'ZPL (Zebra)'),
        ('pdf', 'PDF (A4)'),
    ], string='Tipo de Impressão', required=True, default='zpl')

    def action_print(self):
        self.ensure_one()
        if self.print_type == 'pdf':
            return self.env.ref(
                'mh_stone_reports.action_report_stone_stock_stickers_pdf'
            ).report_action(self.stone_stock_ids)
        else:
            return self.env.ref(
                'mh_stone_reports.action_report_stone_stock_stickers_zpl'
            ).report_action(self.stone_stock_ids)
