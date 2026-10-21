"""Wizard para imprimir etiqueta de tecido numa IoT Box especifica.

Usa o report Studio de tecido e falha com mensagem funcional quando o report
nao existe no ambiente.
"""

from odoo import models, fields, _
from odoo.exceptions import UserError


class ChooseIotPrinterWizardTecido(models.TransientModel):
    _name = 'choose.iot.printer.wizard_tecido'
    _description = 'Escolher Impressora - Etiqueta Tecido'

    picking_id = fields.Many2one('stock.picking', required=True, string="Transferência")
    iot_box_id = fields.Many2one('iot.box', required=True, string="IoT Box")

    def action_confirm_print(self):
        self.ensure_one()

        # XML ID fixo do report Studio de etiqueta de tecido.
        report_name = 'studio_customization.studio_report_docume_9d62d515-ae63-44f2-b236-55c8f03b7ac5'  # Tecido

        report = self.env['ir.actions.report']._get_report_from_name(report_name)
        if not report:
            raise UserError(_('Relatório de etiqueta "Tecido" não encontrado.'))

        # iot_device_id segue o contrato esperado pelos reports IoT.
        return report.with_context({
            'force_print': True,
            'iot_device_id': self.iot_box_id.id,
            'lang': self.env.context.get('lang'),
        }).report_action(self.picking_id)

