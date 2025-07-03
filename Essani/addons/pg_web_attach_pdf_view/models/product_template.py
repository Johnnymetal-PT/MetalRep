from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    attachment_ids = fields.One2many(
        'ir.attachment',
        'res_id',
        domain=[('res_model', '=', 'product.template')],
        string='Documentos'
    )
    all_category_names = fields.Char(compute='_compute_all_category_names')
    
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

    @api.depends('categ_id')
    def _compute_all_category_names(self):
        for product in self:
            category = product.categ_id
            all_names = []
            while category:
                all_names.append(category.name)
                category = category.parent_id
            product.all_category_names = ','.join(all_names)

