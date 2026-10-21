# -*- coding: utf-8 -*-
"""Dados de packing list ao nivel do produto (volumes, pesos e dimensoes).

Define a grelha base (ate 6 tipos de volume) e validacoes para impedir valores
negativos que degradam o calculo logistico.
"""

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Campos principais da packing list
    packing_volumes = fields.Float(
        string='Volumes',
        digits=(4, 2),
        default=0.0,
        help='Número de volumes para este produto'
    )

    packing_gross_weight = fields.Float(
        string='Peso Bruto (Kg)',
        digits=(4, 2),
        default=0.0,
        help='Peso bruto do volume 1 em quilogramas'
    )

    packing_net_weight = fields.Float(
        string='Peso Líquido (Kg)',
        digits=(4, 2),
        default=0.0,
        help='Peso líquido do volume 1 em quilogramas'
    )

    packing_gross_weight_2 = fields.Float(
        string='Peso Bruto 2 (Kg)',
        digits=(4, 2),
        default=0.0,
        help='Peso bruto do volume 2 em quilogramas'
    )

    packing_net_weight_2 = fields.Float(
        string='Peso Líquido 2 (Kg)',
        digits=(4, 2),
        default=0.0,
        help='Peso líquido do volume 2 em quilogramas'
    )

    packing_gross_weight_3 = fields.Float(
        string='Peso Bruto 3 (Kg)',
        digits=(4, 2),
        default=0.0,
        help='Peso bruto do volume 3 em quilogramas'
    )

    packing_net_weight_3 = fields.Float(
        string='Peso Líquido 3 (Kg)',
        digits=(4, 2),
        default=0.0,
        help='Peso líquido do volume 3 em quilogramas'
    )

    packing_gross_weight_4 = fields.Float(
        string='Peso Bruto 4 (Kg)',
        digits=(4, 2),
        default=0.0,
        help='Peso bruto do volume 4 em quilogramas'
    )

    packing_net_weight_4 = fields.Float(
        string='Peso Líquido 4 (Kg)',
        digits=(4, 2),
        default=0.0,
        help='Peso líquido do volume 4 em quilogramas'
    )

    packing_gross_weight_5 = fields.Float(
        string='Peso Bruto 5 (Kg)',
        digits=(4, 2),
        default=0.0,
        help='Peso bruto do volume 5 em quilogramas'
    )

    packing_net_weight_5 = fields.Float(
        string='Peso Líquido 5 (Kg)',
        digits=(4, 2),
        default=0.0,
        help='Peso líquido do volume 5 em quilogramas'
    )

    packing_gross_weight_6 = fields.Float(
        string='Peso Bruto 6 (Kg)',
        digits=(4, 2),
        default=0.0,
        help='Peso bruto do volume 6 em quilogramas'
    )

    packing_net_weight_6 = fields.Float(
        string='Peso Líquido 6 (Kg)',
        digits=(4, 2),
        default=0.0,
        help='Peso líquido do volume 6 em quilogramas'
    )

    packing_weight_2 = fields.Float(
        string='Peso 2 (Kg)',
        digits=(4, 2),
        default=0.0,
        help='Peso do volume 2 em quilogramas'
    )

    packing_weight_3 = fields.Float(
        string='Peso 3 (Kg)',
        digits=(4, 2),
        default=0.0,
        help='Peso do volume 3 em quilogramas'
    )

    packing_weight_4 = fields.Float(
        string='Peso 4 (Kg)',
        digits=(4, 2),
        default=0.0,
        help='Peso do volume 4 em quilogramas'
    )

    packing_weight_5 = fields.Float(
        string='Peso 5 (Kg)',
        digits=(4, 2),
        default=0.0,
        help='Peso do volume 5 em quilogramas'
    )

    packing_weight_6 = fields.Float(
        string='Peso 6 (Kg)',
        digits=(4, 2),
        default=0.0,
        help='Peso do volume 6 em quilogramas'
    )

    # Número de volumes por tipo
    packing_number_1 = fields.Integer(string='Nº Volumes Tipo 1', default=0)
    packing_number_2 = fields.Integer(string='Nº Volumes Tipo 2', default=0)
    packing_number_3 = fields.Integer(string='Nº Volumes Tipo 3', default=0)
    packing_number_4 = fields.Integer(string='Nº Volumes Tipo 4', default=0)
    packing_number_5 = fields.Integer(string='Nº Volumes Tipo 5', default=0)
    packing_number_6 = fields.Integer(string='Nº Volumes Tipo 6', default=0)

    packing_cubicagem = fields.Float(
        string='Cubicagem',
        digits=(4, 2),
        default=0.0,
        help='Cubicagem total em m³ (informada manualmente)'
    )

    # Dimensões do primeiro volume (sempre visível)
    packing_comprimento = fields.Float(string='Comprimento', digits=(4, 2), default=0.0)
    packing_altura = fields.Float(string='Altura', digits=(4, 2), default=0.0)
    packing_largura = fields.Float(string='Largura', digits=(4, 2), default=0.0)

    # Volume 2
    packing_comprimento_2 = fields.Float(string='Comprimento 2', digits=(4, 2), default=0.0)
    packing_altura_2 = fields.Float(string='Altura 2', digits=(4, 2), default=0.0)
    packing_largura_2 = fields.Float(string='Largura 2', digits=(4, 2), default=0.0)

    # Volume 3
    packing_comprimento_3 = fields.Float(string='Comprimento 3', digits=(4, 2), default=0.0)
    packing_altura_3 = fields.Float(string='Altura 3', digits=(4, 2), default=0.0)
    packing_largura_3 = fields.Float(string='Largura 3', digits=(4, 2), default=0.0)

    # Volume 4
    packing_comprimento_4 = fields.Float(string='Comprimento 4', digits=(4, 2), default=0.0)
    packing_altura_4 = fields.Float(string='Altura 4', digits=(4, 2), default=0.0)
    packing_largura_4 = fields.Float(string='Largura 4', digits=(4, 2), default=0.0)

    # Volume 5
    packing_comprimento_5 = fields.Float(string='Comprimento 5', digits=(4, 2), default=0.0)
    packing_altura_5 = fields.Float(string='Altura 5', digits=(4, 2), default=0.0)
    packing_largura_5 = fields.Float(string='Largura 5', digits=(4, 2), default=0.0)

    # Volume 6
    packing_comprimento_6 = fields.Float(string='Comprimento 6', digits=(4, 2), default=0.0)
    packing_altura_6 = fields.Float(string='Altura 6', digits=(4, 2), default=0.0)
    packing_largura_6 = fields.Float(string='Largura 6', digits=(4, 2), default=0.0)

    # Validações

    @api.constrains('packing_volumes')
    def _check_volumes_range(self):
        # Regra base: modulo nao aceita valores negativos; limite superior (6)
        # e controlado por UI/processo e pode ser reativado aqui se necessario.
        for record in self:
            if record.packing_volumes < 0:
                raise ValidationError("O número de volumes não pode ser negativo.")
            # if record.packing_volumes > 6:
            #     raise ValidationError("O número máximo de volumes suportado é 6.")

    @api.constrains('packing_gross_weight', 'packing_net_weight',
                     'packing_gross_weight_2', 'packing_net_weight_2',
                     'packing_gross_weight_3', 'packing_net_weight_3',
                     'packing_gross_weight_4', 'packing_net_weight_4',
                     'packing_gross_weight_5', 'packing_net_weight_5',
                     'packing_gross_weight_6', 'packing_net_weight_6')
    def _check_weight_positive(self):
        # Validacao transversal para todos os slots de peso (1..6).
        for record in self:
            weight_fields = [
                'packing_gross_weight', 'packing_net_weight',
                'packing_gross_weight_2', 'packing_net_weight_2',
                'packing_gross_weight_3', 'packing_net_weight_3',
                'packing_gross_weight_4', 'packing_net_weight_4',
                'packing_gross_weight_5', 'packing_net_weight_5',
                'packing_gross_weight_6', 'packing_net_weight_6'
            ]
            for field_name in weight_fields:
                if getattr(record, field_name, 0.0) < 0:
                    raise ValidationError(
                        f"O peso '{record._fields[field_name].string}' não pode ser negativo."
                    )

    @api.constrains('packing_comprimento', 'packing_altura', 'packing_largura',
                    'packing_comprimento_2', 'packing_altura_2', 'packing_largura_2',
                    'packing_comprimento_3', 'packing_altura_3', 'packing_largura_3',
                    'packing_comprimento_4', 'packing_altura_4', 'packing_largura_4',
                    'packing_comprimento_5', 'packing_altura_5', 'packing_largura_5',
                    'packing_comprimento_6', 'packing_altura_6', 'packing_largura_6')
    def _check_dimensions_positive(self):
        # Evita dimensoes invalidas que distorcem cubicagem e documentos logisticos.
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
