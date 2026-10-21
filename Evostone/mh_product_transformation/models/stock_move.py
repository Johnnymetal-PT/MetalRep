from odoo import models, fields


class StockMove(models.Model):
    _inherit = 'stock.move'

    transformation_output_line_id = fields.Many2one(
        'transformation.line.output',
        string='Linha de Output',
        help='Linha de output de transformação que gerou este movimento'
    )

    transformation_id = fields.Many2one(
        'transformation.document',
        string='Documento de Transformação',
        index=True,
        help='Documento de transformação associado a este movimento'
    )
