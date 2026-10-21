# -*- coding: utf-8 -*-
"""Documentos do produto (anexos) e o seu agrupamento para apresentação no website.

Ver o __manifest__.py para o contexto completo do módulo.
"""
from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Anexos ligados ao próprio produto (res_model = product.template, res_id = id do produto).
    attachment_ids = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'product.template')], string='Documentos')

    def _get_document_groups(self):
        # Organiza os documentos em secções para a página web. A classificação é feita
        # por palavra-chave no NOME do ficheiro; tudo o resto cai em "OUTROS".
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


