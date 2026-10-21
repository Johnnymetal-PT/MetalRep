"""Classificacao do fornecedor para o report Listagem.

O report Listagem (pg_listagem_report) usa ``pg_componente_tipo`` para
saber em que seccao da coluna "Material em Falta" colocar o componente.
Sem classificacao -> componente nao aparece no report.
"""
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    pg_componente_tipo = fields.Selection(
        [
            ('casco', 'Casco'),
            ('tecido', 'Tecido'),
            ('polimento', 'Polimento'),
        ],
        string='Tipo de Componente Fornecido',
        help='Classifica este fornecedor para o report Listagem. '
             'Componentes da MO cujo fornecedor principal tenha este campo '
             'preenchido aparecem na coluna "Material em Falta" agrupados. '
             'Mapeamento dos grupos no report: Casco -> ESTRUTURA, '
             'Tecido -> TECIDO, Polimento -> ACABAMENTO. '
             'Sem valor -> componente nao aparece no report.',
    )
