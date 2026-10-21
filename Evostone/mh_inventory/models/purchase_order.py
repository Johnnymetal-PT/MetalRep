from odoo import models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # Campos service_type, import_document_ids e transformation_document_ids
    # estão definidos no módulo mh_base
    # Este módulo apenas herda e pode adicionar funcionalidades extras se necessário
    pass
