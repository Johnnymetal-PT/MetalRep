"""Modelo mestre da tabela de consumos por variante/subvariante de tecido.

Cada registo representa uma combinacao de "FABRIC USED IN X" + subvariante,
com consumos definidos para quantidades de 1 a 10 unidades.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import re

_logger = logging.getLogger(__name__)

class FabricVariant(models.Model):
    _name = 'fabric.variant'
    _description = 'Variante de Tecido'
    _order = 'variant_id, subvariant_name'
    
    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Produto',
        required=True,
        ondelete='cascade',
        help='Produto de tecido ao qual esta variante pertence'
    )
    
    variant_id = fields.Integer(
        string='ID da Variante',
        compute='_compute_variant_id_from_attribute',
        store=True,
        readonly=True,
        help='Número da variante (1, 2, 3) extraído do Atributo da Variante'
    )
    
    variant_attribute_id = fields.Many2one(
        'product.attribute',
        string='Atributo da Variante',
        required=True,
        domain="[('name', 'ilike', 'FABRIC USED IN')]",
        help='Atributo de produto ao qual esta variante pertence (ex: "FABRIC USED IN 1")'
    )

    variant_name = fields.Char(
        string='Nome da Variante',
        related='variant_attribute_id.name',
        store=True,
        readonly=True,
        help='Nome completo da variante (ex: "FABRIC USED IN 1")'
    )

    # CORREÇÃO: subvariant_value_id volta a ser o Many2one direto que o utilizador seleciona
    subvariant_value_id = fields.Many2one(
        "product.attribute.value",
        string="Valor da Subvariante",
        required=True,
        # O domínio será definido na vista XML para filtrar com base em variant_attribute_id
        help='Valor do atributo de produto para a subvariante (Total, Costas, Assento, etc.)'
    )

    # CORREÇÃO: subvariant_name é agora um campo computado a partir de subvariant_value_id.name
    # Isto evita o problema do JSONB encontrado anteriormente.
    subvariant_name = fields.Char(
        string='Nome da Subvariante',
        compute='_compute_subvariant_name',
        store=True, # Armazenar como texto simples
        readonly=True, # Não deve ser editável diretamente pelo utilizador
        help='Nome da subvariante (Total, Costas, Assento, etc.)'
    )

    # NOVO/REINSTAURADO método compute para subvariant_name
    @api.depends('subvariant_value_id')
    def _compute_subvariant_name(self):
        for record in self:
            record.subvariant_name = record.subvariant_value_id.name if record.subvariant_value_id else False

    variant_reference = fields.Char(
        string='Referência da Variante',
        compute='_compute_variant_reference',
        store=True,
        help='Referência completa da variante (ex: "FABRIC USED IN 1: Total")'
    )

    consumption_1 = fields.Float(string="1", default=0.0)
    consumption_2 = fields.Float(string="2", default=0.0)
    consumption_3 = fields.Float(string="3", default=0.0)
    consumption_4 = fields.Float(string="4", default=0.0)
    consumption_5 = fields.Float(string="5", default=0.0)
    consumption_6 = fields.Float(string="6", default=0.0)
    consumption_7 = fields.Float(string="7", default=0.0)
    consumption_8 = fields.Float(string="8", default=0.0)
    consumption_9 = fields.Float(string="9", default=0.0)
    consumption_10 = fields.Float(string="10", default=0.0)

    _sql_constraints = [
        ('unique_variant_subvariant', 
         # A restrição de unicidade deve usar os campos Many2one para garantir a unicidade
         'UNIQUE(product_tmpl_id, variant_attribute_id, subvariant_value_id)',
         'Já existe uma tabela para esta combinação de variante e subvariante!')
    ]

    @api.depends('variant_attribute_id')
    def _compute_variant_id_from_attribute(self):
        # Contrato de nomenclatura: extrai "X" de "FABRIC USED IN X".
        # Se o atributo nao seguir o padrao, variant_id fica vazio.
        for record in self:
            if record.variant_attribute_id:
                match = re.search(r'FABRIC USED IN (\d+)', record.variant_attribute_id.name, re.IGNORECASE)
                record.variant_id = int(match.group(1)) if match else False
            else:
                record.variant_id = False

    @api.depends('variant_id', 'subvariant_name')
    def _compute_variant_reference(self):
        for record in self:
            if record.variant_id and record.subvariant_name:
                record.variant_reference = f"FABRIC USED IN {record.variant_id}: {record.subvariant_name}"
            else:
                record.variant_reference = False

    # REMOVIDO: _get_subvariant_name_options não é mais necessário, pois não usamos fields.Selection
    # REMOVIDO: _compute_subvariant_value_id e _inverse_subvariant_value_id não são mais necessários
    # pois subvariant_value_id é um Many2one direto.

    @api.onchange('variant_attribute_id')
    def _onchange_variant_attribute_id(self):
        # Quando variant_attribute_id muda, limpa subvariant_value_id
        # O domínio na XML irá então filtrar as opções para subvariant_value_id
        self.subvariant_value_id = False
        # subvariant_name será recomputado automaticamente quando subvariant_value_id for definido

    def get_consumption_for_quantity(self, quantity):
        # Regra de tabela: 1..10 por indice; acima de 10 usa ultima coluna.
        self.ensure_one()
        consumption_table = [
            self.consumption_1, self.consumption_2, self.consumption_3,
            self.consumption_4, self.consumption_5, self.consumption_6,
            self.consumption_7, self.consumption_8, self.consumption_9,
            self.consumption_10
        ]
        qty_index = int(quantity) - 1 
        if 0 <= qty_index < len(consumption_table):
            return consumption_table[qty_index]
        return consumption_table[-1] if quantity > 10 else 0.0
