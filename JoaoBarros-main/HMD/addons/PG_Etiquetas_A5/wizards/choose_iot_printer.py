import logging
from odoo import models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ChooseIotPrinterWizard(models.TransientModel):
    _name = 'choose.iot.printer.wizard'
    _description = 'Choose IoT Box for ZPL Labels'

    picking_id = fields.Many2one('stock.picking', required=True)
    iot_box_id = fields.Many2one('iot.box', string="IoT Box", required=True)

    def action_confirm_print(self):
        picking = self.picking_id
        _logger.info("ZPL print requested for picking: %s", picking.name)

        # Coletar movimentos com etiquetas ZPL
        zpl_move_ids = []
        for move in picking.move_ids.filtered(
            lambda m: m.product_uom_qty > 0 and m.product_id.print_label_type == 'ZPL'
        ):
            zpl_move_ids.extend([move.id] * int(move.product_uom_qty))

        if not zpl_move_ids:
            raise UserError("Não foram encontradas etiquetas ZPL para imprimir.")

        _logger.info("Found %d ZPL move(s) to print.", len(zpl_move_ids))

        # Procurar relatório correto
        report_ref = 'studio_customization.studio_report_docume_ee312668-34d8-4791-bf96-c8381ed8abac'
        report = self.env['ir.actions.report'].search([
            ('report_name', '=', report_ref),
        ], limit=1)

        if not report:
            raise UserError("Relatório de etiquetas ZPL não encontrado.")

        _logger.info("Usando report_action para envio nativo do Odoo via IoT Box associada.")

        # Força contexto para usar a IoT Box escolhida
        return report.with_context(
            iot_device_id=self.iot_box_id.id,
            lang=self.env.user.lang
        ).report_action(zpl_move_ids)
