import base64
from io import BytesIO
from PyPDF2 import PdfMerger
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    print_label_type = fields.Selection([
        ('A5', 'A5 Label'),
        ('5x8', '5x8 Label'),
        ('ZPL', 'ZPL Label'),
    ], string="Label Print Type", default='ZPL')

    def action_print_a5_studio_label(self):
        report = self.env["ir.actions.report"].search([
            ("report_name", "=", "studio_customization.studio_report_docume_52767c0b-fd5e-41c6-9934-c0875e4b4227"),
        ], limit=1)
        return report.report_action(self)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    print_label_type = fields.Selection(
        related='product_tmpl_id.print_label_type',
        store=True,
        readonly=False
    )

    def action_print_a5_studio_label(self):
        report = self.env["ir.actions.report"].search([
            ("report_name", "=", "studio_customization.studio_report_docume_4d3ac47d-eb3c-4172-873a-69ef757664d3"),
        ], limit=1)
        return report.report_action(self)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    has_zpl_labels = fields.Boolean(
        string="Contains ZPL Labels",
        compute='_compute_has_zpl_labels'
    )

    @api.depends('move_ids.product_id.print_label_type', 'move_line_ids.product_id.print_label_type')
    def _compute_has_zpl_labels(self):
        for picking in self:
            moves = picking._get_label_moves()
            picking.has_zpl_labels = any(
                move.product_id.print_label_type == 'ZPL'
                for move in moves
            )

    def _get_label_moves(self):
        self.ensure_one()

        moves = self.move_ids.filtered(lambda m: m.state != 'cancel')
        if moves:
            return moves

        # When the picking is still in draft, the stock moves may not yet be
        # materialised in ``move_ids``. In that case rely on the operations to
        # recover their linked moves so that we can still print labels.
        move_lines = self.move_line_ids or self.move_ids_without_package
        if move_lines:
            return move_lines.mapped('move_id').filtered(lambda m: m and m.state != 'cancel')

        return moves

    def _get_move_label_qty(self, move):
        self.ensure_one()

        qty = (
            move.product_uom_qty
            or getattr(move, 'quantity_done', 0)
            or move.reserved_availability
        )
        if not qty and move.move_line_ids:
            qty = sum(move.move_line_ids.mapped('qty_done'))

        return int(qty or 0)

    def action_open_zpl_printer(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Escolher Impressora ZPL',
            'res_model': 'choose.iot.printer.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_picking_id': self.id,
            }
        }


    def action_print_received_labels(self):
        self.ensure_one()

        label_batches = {'A5': [], '5x8': [], 'ZPL': []}
        label_report_map = {
            'A5': 'studio_customization.studio_report_docume_6dda9565-82b4-45bc-ba88-b0a65488eb95',
            '5x8': 'studio_customization.studio_report_docume_494c29ed-77e4-466a-adf4-30274ce43580',
        }

        moves = self._get_label_moves()
        for move in moves:
            qty = self._get_move_label_qty(move)
            label_type = move.product_id.print_label_type
            if qty > 0 and label_type in label_batches:
                label_batches[label_type].extend([move.id] * qty)

        pdf_merger = PdfMerger()
        pdf_added = False

        for label_type in ['A5', '5x8']:
            move_ids = label_batches[label_type]
            if not move_ids:
                continue

            report_name = label_report_map[label_type]
            pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(report_name, move_ids)

            # Fix for PyPDF2 2.0.12 compatibility
            stream = BytesIO(pdf_content)
            stream.seek(0)  # <<< Important!
            pdf_merger.append(stream)
            pdf_added = True

        if not pdf_added:
            raise UserError("Não foram encontradas etiquetas A5/8x5 para imprimir.")

        final_buffer = BytesIO()
        pdf_merger.write(final_buffer)
        final_buffer.seek(0)  # <<< Important too!
        pdf_merger.close()

        attachment = self.env['ir.attachment'].create({
            'name': f"{self.name}_Labels_ALL.pdf",
            'type': 'binary',
            'datas': base64.b64encode(final_buffer.read()),
            'res_model': 'stock.picking',
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
        


