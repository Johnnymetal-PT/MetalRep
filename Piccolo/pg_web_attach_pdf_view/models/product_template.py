"""Anexos do produto agrupados por categoria documental.

Disponibiliza ao QWeb da pagina publica do produto:
- ``attachment_ids``: lista de ir.attachment ligados a este template;
- ``_get_document_groups()``: agrupa anexos por palavra-chave no
  ``name`` (ficha tecnica, certificado, 3D, outros);
- ``_get_attachment_description()``: helper para obter description
  de um anexo dado o id.

Convencao de nomeacao usada (case-sensitive, MAIUSCULAS):
  - "3D" -> grupo "3D"
  - "CERTIFICADO" -> "CERTIFICADO DE CONFORMIDADE"
  - "FICHA" -> "FICHA TECNICA"
  - resto -> "OUTROS"
"""
from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Dominio fixa ``res_model='product.template'``; se algum anexo
    # estiver ligado a ``product.product`` em vez de template, nao
    # aparece aqui (intencional: queremos a visao do template).
    attachment_ids = fields.One2many(
        'ir.attachment', 'res_id',
        domain=[('res_model', '=', 'product.template')],
        string='Documentos',
    )

    def _get_document_groups(self):
        """Agrupa ``attachment_ids`` em 4 categorias para o QWeb.

        Match e case-sensitive (MAIUSCULAS) - parte da convencao
        Piccolo de nomear ficheiros em maiusculas.
        """
        self.ensure_one()
        groups = {
            'FICHA TÉCNICA': [],
            'CERTIFICADO DE CONFORMIDADE': [],
            '3D': [],
            'OUTROS': [],
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
        # Helper para QWeb obter a description de um anexo a partir
        # do id (evita ter que dereferenciar attachment_ids na vista).
        attachment = self.env['ir.attachment'].browse(attachment_id)
        return attachment.description
