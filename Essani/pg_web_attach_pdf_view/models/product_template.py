"""Campos e helpers que agregam documentos do template e das variantes para o website."""
from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.product'

    x_studio_referncia_interna = fields.Char()
    
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_template_image_ids = fields.One2many(
        'product.image',
        'product_tmpl_id',
        domain=[('product_variant_id', '=', False)],
    )

    attachment_ids = fields.One2many(
        'ir.attachment',
        'res_id',
        domain=[('res_model', '=', 'product.template')],
        string='Documentos'
    )
    website_attachment_ids = fields.Many2many(
        'ir.attachment',
        compute='_compute_website_attachment_ids',
        string='Website Documents'
    )
    all_category_names = fields.Char(compute='_compute_all_category_names')
    
    @api.depends('attachment_ids', 'product_variant_ids')
    def _compute_website_attachment_ids(self):
        for product in self:
            variant_ids = product.product_variant_ids.ids
            domain = [
                '|',
                '&', ('res_model', '=', 'product.template'), ('res_id', '=', product.id),
                '&', ('res_model', '=', 'product.product'), ('res_id', 'in', variant_ids),
            ]
            product.website_attachment_ids = self.env['ir.attachment'].search(domain)

    def _get_images(self):
        images = super()._get_images()
        if hasattr(images, "filtered"):
            return images.filtered(lambda img: not img.product_variant_id)
        return [img for img in images if not getattr(img, "product_variant_id", False)]

    def _get_document_groups(self):
        self.ensure_one()
        groups = {
            'FICHA TÉCNICA': [],
            'CERTIFICADO DE CONFORMIDADE': [],
            '3D': [],
            'OUTROS': []
        }
        for doc in self.website_attachment_ids:
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


