from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    attachment_ids = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'product.template')], string='Documentos')

    def _get_document_groups(self):
        self.ensure_one()
        groups = {
            'FICHA TÉCNICA': [],
            'CERTIFICADO DE CONFORMIDADE': [],
            '3D': [],
            'OUTROS': []
        }
        for doc in self.attachment_ids:
            if '3D' in doc.name:
                groups['3D'].append(doc)
            elif 'CERTIFICADO' in doc.name:
                groups['CERTIFICADO DE CONFORMIDADE'].append(doc)
            elif 'FICHA' in doc.name:
                groups['FICHA TÉCNICA'].append(doc)
            else:
                groups['OUTROS'].append(doc)
        return groups

    def _get_attachment_description(self, attachment_id):

        attachment = self.env['ir.attachment'].browse(attachment_id)
        return attachment.description


