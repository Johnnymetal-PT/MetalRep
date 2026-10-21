# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductCategory(models.Model):
    _inherit = 'product.category'

    property_cost_method = fields.Selection(
        selection_add=[
            ('pcmp', 'PCMP (Legado - não utilizar)')
        ],
        ondelete={'pcmp': 'set average'},
        help="""Standard Price: Os produtos são valorizados ao custo padrão definido no produto.
Average Cost (AVCO): Os produtos são valorizados ao custo médio ponderado.
First In First Out (FIFO): Os produtos são valorizados assumindo que os primeiros a entrar são os primeiros a sair.
PCMP (Ano Fiscal): Os produtos são valorizados pelo Preço de Custo Médio Ponderado com base no ano fiscal.""",
    )

    @api.model_create_multi
    def create(self, vals_list):
        if any(vals.get('property_cost_method') == 'pcmp' for vals in vals_list):
            raise ValidationError(_(
                "O método PCMP legado foi descontinuado. Utilize o Custo Médio (AVCO) standard do Odoo."
            ))
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('property_cost_method') == 'pcmp':
            raise ValidationError(_(
                "O método PCMP legado foi descontinuado. Utilize o Custo Médio (AVCO) standard do Odoo."
            ))
        return super().write(vals)
