# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Campos principais da packing list
    packing_volumes = fields.Float(
        string='Volumes',
        digits=(4, 2),
        related='x_studio_volumes',
        readonly=False,
        store=True,
        help='Número de volumes para este produto'
    )

    packing_weight = fields.Float(
        string='Peso (Kg)',
        digits=(4, 2),
        related='x_studio_peso_kg_1',
        readonly=False,
        store=True,
        help='Peso total em quilogramas'
    )

    x_studio_cubicagem = fields.Float(
        compute='_compute_packing_cubicagem',
        store=True,
        readonly=False,
    )

    packing_cubicagem = fields.Float(
        string='Cubicagem',
        digits=(4, 2),
        related='x_studio_cubicagem',
        readonly=False,
        store=True,
        help='Cubicagem total em m³ calculada automaticamente'
    )

    # Dimensões do primeiro volume (sempre visível)
    packing_comprimento = fields.Float(string='Comprimento', digits=(4, 2), related='x_studio_comprimento', readonly=False, store=True)
    packing_altura = fields.Float(string='Altura', digits=(4, 2), related='x_studio_altura', readonly=False, store=True)
    packing_largura = fields.Float(string='Largura', digits=(4, 2), related='x_studio_largura', readonly=False, store=True)

    # Volume 2
    packing_comprimento_2 = fields.Float(string='Comprimento 2', digits=(4, 2), related='x_studio_comprimento_2', readonly=False, store=True)
    packing_altura_2 = fields.Float(string='Altura 2', digits=(4, 2), related='x_studio_altura_2', readonly=False, store=True)
    packing_largura_2 = fields.Float(string='Largura 2', digits=(4, 2), related='x_studio_largura_2', readonly=False, store=True)

    # Volume 3
    packing_comprimento_3 = fields.Float(string='Comprimento 3', digits=(4, 2), related='x_studio_comprimento_3', readonly=False, store=True)
    packing_altura_3 = fields.Float(string='Altura 3', digits=(4, 2), related='x_studio_altura_3', readonly=False, store=True)
    packing_largura_3 = fields.Float(string='Largura 3', digits=(4, 2), related='x_studio_largura_3', readonly=False, store=True)

    # Volume 4
    packing_comprimento_4 = fields.Float(string='Comprimento 4', digits=(4, 2), related='x_studio_comprimento_4', readonly=False, store=True)
    packing_altura_4 = fields.Float(string='Altura 4', digits=(4, 2), related='x_studio_altura_4', readonly=False, store=True)
    packing_largura_4 = fields.Float(string='Largura 4', digits=(4, 2), related='x_studio_largura_4', readonly=False, store=True)

    # Volume 5
    packing_comprimento_5 = fields.Float(string='Comprimento 5', digits=(4, 2), related='x_studio_comprimento_5', readonly=False, store=True)
    packing_altura_5 = fields.Float(string='Altura 5', digits=(4, 2), related='x_studio_altura_5', readonly=False, store=True)
    packing_largura_5 = fields.Float(string='Largura 5', digits=(4, 2), related='x_studio_largura_5', readonly=False, store=True)

    # Volume 6
    packing_comprimento_6 = fields.Float(string='Comprimento 6', digits=(4, 2), related='x_studio_comprimento_6', readonly=False, store=True)
    packing_altura_6 = fields.Float(string='Altura 6', digits=(4, 2), related='x_studio_altura_6', readonly=False, store=True)
    packing_largura_6 = fields.Float(string='Largura 6', digits=(4, 2), related='x_studio_largura_6', readonly=False, store=True)

    # Validações

    @api.constrains('packing_volumes')
    def _check_volumes_range(self):
        for record in self:
            if record.packing_volumes < 0:
                raise ValidationError("O número de volumes não pode ser negativo.")
            if record.packing_volumes > 6:
                raise ValidationError("O número máximo de volumes suportado é 6.")

    @api.constrains('packing_weight')
    def _check_weight_positive(self):
        for record in self:
            if record.packing_weight < 0:
                raise ValidationError("O peso não pode ser negativo.")

    @api.constrains('packing_comprimento', 'packing_altura', 'packing_largura',
                    'packing_comprimento_2', 'packing_altura_2', 'packing_largura_2',
                    'packing_comprimento_3', 'packing_altura_3', 'packing_largura_3',
                    'packing_comprimento_4', 'packing_altura_4', 'packing_largura_4',
                    'packing_comprimento_5', 'packing_altura_5', 'packing_largura_5',
                    'packing_comprimento_6', 'packing_altura_6', 'packing_largura_6')
    def _check_dimensions_positive(self):
        for record in self:
            dimension_fields = [
                'packing_comprimento', 'packing_altura', 'packing_largura',
                'packing_comprimento_2', 'packing_altura_2', 'packing_largura_2',
                'packing_comprimento_3', 'packing_altura_3', 'packing_largura_3',
                'packing_comprimento_4', 'packing_altura_4', 'packing_largura_4',
                'packing_comprimento_5', 'packing_altura_5', 'packing_largura_5',
                'packing_comprimento_6', 'packing_altura_6', 'packing_largura_6'
            ]
            for field_name in dimension_fields:
                if getattr(record, field_name, 0.0) < 0:
                    raise ValidationError(
                        f"A dimensão '{record._fields[field_name].string}' não pode ser negativa."
                    )

    @api.depends(
        'packing_volumes',
        'packing_comprimento', 'packing_altura', 'packing_largura',
        'packing_comprimento_2', 'packing_altura_2', 'packing_largura_2',
        'packing_comprimento_3', 'packing_altura_3', 'packing_largura_3',
        'packing_comprimento_4', 'packing_altura_4', 'packing_largura_4',
        'packing_comprimento_5', 'packing_altura_5', 'packing_largura_5',
        'packing_comprimento_6', 'packing_altura_6', 'packing_largura_6')
    def _compute_packing_cubicagem(self):
        """Calcula automaticamente a cubicagem baseada nas dimensões informadas"""
        for product in self:
            total = 0.0
            dims = [
                (product.packing_comprimento, product.packing_altura, product.packing_largura),
                (product.packing_comprimento_2, product.packing_altura_2, product.packing_largura_2),
                (product.packing_comprimento_3, product.packing_altura_3, product.packing_largura_3),
                (product.packing_comprimento_4, product.packing_altura_4, product.packing_largura_4),
                (product.packing_comprimento_5, product.packing_altura_5, product.packing_largura_5),
                (product.packing_comprimento_6, product.packing_altura_6, product.packing_largura_6),
            ]
            for i in range(int(min(6, product.packing_volumes))):
                c, a, l = dims[i]
                total += c * a * l
            product.x_studio_cubicagem = total

