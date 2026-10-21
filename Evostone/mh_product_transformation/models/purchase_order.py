from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # Campos service_type e import_document_ids estão definidos no módulo mh_base
    # Este módulo define transformation_document_ids (relação com seu próprio modelo)

    # Relação inversa com transformation.document
    transformation_document_ids = fields.Many2many(
        'transformation.document',
        'transformation_service_purchase_rel',
        'purchase_order_id',
        'transformation_id',
        string='Documentos de Transformação'
    )