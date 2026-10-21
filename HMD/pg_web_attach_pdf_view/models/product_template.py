# -*- coding: utf-8 -*-
"""Suporte aos documentos do produto no front website.

Adiciona ao `product.template`:
- `attachment_ids`: anexos visiveis na aba Documentos.
- `all_category_names`: cadeia das categorias hierarquicas.
- `_get_document_groups`: arruma anexos por grupo (3D / Imagens HR /
  Ficha Tecnica) por MATCH no nome do anexo - convencao HMD.

Ver `__manifest__.py` para o guia completo, incluindo a convencao de
nomes dos anexos para filtragem por variante.
"""

from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    attachment_ids = fields.Many2many(
        'ir.attachment',
        'res_id',
        string='Documentos',
        domain=[('res_model', '=', 'product.template')],
        help='Attachments linked to the product template.'
    )
    all_category_names = fields.Char(compute='_compute_all_category_names')

    def _get_document_groups(self):
        """Agrupa `attachment_ids` em 3 baldes pelo nome do anexo.

        Convencao HMD: o nome do anexo deve comecar pelo grupo
        ('FICHA TECNICA', 'HR', '3D') e usar ' » ' como separador
        hierarquico para o JS do template filtrar por variante (ver FAQ
        no manifest).

        2026-07-29: o balde 'CERTIFICADO DE CONFORMIDADE' foi substituido
        por 'IMAGENS HR' (imagens de alta resolucao) a pedido da HMD, para
        os 3 downloads da pagina de produto pedidos na tarefa 6604. A troca
        e segura: nao existia 1 unico anexo com 'CERTIFICADO' no nome
        (0 em 4060 anexos de product.template, verificado em producao).

        ATENCAO ao match do grupo HR: 'HR' como substring da falsos
        positivos ('VALCHROMAT' contem 'HR' - caso real na base). Por isso
        este balde exige que o nome COMECE por 'HR', ao contrario dos
        outros dois, que mantem substring por compatibilidade.
        """
        self.ensure_one()
        # HARDCODED: rotulos em PT. Se for preciso i18n, evoluir.
        groups = {
            'FICHA TÉCNICA': [],
            'IMAGENS HR': [],
            '3D': [],
        }
        for doc in self.attachment_ids:
            # Ordem importa: '3D' primeiro (substring curta), depois HR
            # (prefixo), depois FICHA. Anexo sem nenhuma destas marcas
            # NAO aparece - silencioso por design.
            if '3D' in doc.name:
                groups['3D'].append(doc)
            elif doc.name.startswith('HR'):
                groups['IMAGENS HR'].append(doc)
            elif 'FICHA' in doc.name:
                groups['FICHA TÉCNICA'].append(doc)
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

