from odoo import models, fields, _
from odoo.exceptions import UserError


class ChooseIotPrinterWizardEntrega(models.TransientModel):
    _name = 'choose.iot.printer.wizard'
    _description = 'Escolher Impressora - Etiqueta Entrega'

    picking_id = fields.Many2one('stock.picking', required=True, string="Transferência")
    iot_box_id = fields.Many2one('iot.box', required=True, string="IoT Box")

    def action_confirm_print(self):
        self.ensure_one()

        report_name = 'studio_customization.studio_report_docume_03a04fe9-992d-4af4-b03b-1347317aaae0'  # Entrega

        report = self.env['ir.actions.report']._get_report_from_name(report_name)
        if not report:
            raise UserError(_('Relatório de etiqueta "Entrega" não encontrado.'))

        return report.with_context({
            'force_print': True,
            'iot_device_id': self.iot_box_id.id,
            'lang': self.env.context.get('lang'),
        }).report_action(self.picking_id)
