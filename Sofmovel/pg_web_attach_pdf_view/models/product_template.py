"""Anexos do produto agrupados por tipo e cadeia de categorias.

Pertence ao modulo `pg_web_attach_pdf_view`. Le `ir.attachment` ligados a
`product.template` e devolve-os agrupados por nome (FICHA / CERTIFICADO /
3D / OUTROS). O agrupamento e por palavra-chave case-sensitive.
"""
from odoo import models, fields, api

class ProductTemplate(models.Model):
    """Adiciona anexos, grupos de documentos e cadeia de categorias."""

    _inherit = 'product.template'

    attachment_ids = fields.One2many(
        'ir.attachment',
        'res_id',
        domain=[('res_model', '=', 'product.template')],
        string='Documentos'
    )
    all_category_names = fields.Char(compute='_compute_all_category_names')

    def _get_document_groups(self):
        """Agrupa attachments por palavra-chave no nome do ficheiro.

        IMPORTANTE: o match e case-sensitive (`'FICHA' in name`). Ficheiros
        com palavras-chave em minusculas caem em OUTROS.
        """
        self.ensure_one()
        groups = {
            'FICHA TÉCNICA': [],
            'CERTIFICADO DE CONFORMIDADE': [],
            '3D': [],
            'OUTROS': []
        }
        for doc in self.attachment_ids:
            # Ordem importa: "3D" tem prioridade sobre os restantes grupos.
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

