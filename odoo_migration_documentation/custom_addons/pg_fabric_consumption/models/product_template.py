"""Extensoes de produto e validacoes de atributos para consumo de tecido.

Concentra a logica de identificacao de tecidos, leitura de variantes e calculo
de consumo agregado por subvariantes escolhidas na venda.
"""

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import logging
import re

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    # Campo para identificar produtos de tecido
    is_fabric = fields.Boolean(
        string='É Tecido?', 
        default=False,
        help='Marque esta opção se este produto for um tecido usado em produtos configuráveis'
    )
    
    # Novo campo para identificar o tecido na descrição da ordem de venda
    fabric_identifier_id = fields.Integer(
        string='Identificador de Tecido',
        help='Número identificador para este tecido (ex: 1 para FABRIC 1, 2 para FABRIC 2). Usado para ligar à descrição da ordem de venda.',
        copy=False,
    )

    # Relação One2many com as variantes de tecido
    fabric_variant_ids = fields.One2many(
        'fabric.variant', 
        'product_tmpl_id', 
        string='Variantes de Tecido',
        help='Tabelas de consumo de tecido por variante e subvariante'
    )
    
    _sql_constraints = [
        ('fabric_identifier_id_required_if_fabric',
         'CHECK(NOT is_fabric OR fabric_identifier_id IS NOT NULL)',
         'O campo "Identificador de Tecido" é obrigatório para produtos de tecido.')
    ]

    @api.model
    def get_fabric_variants_from_attributes(self, fabric_product_tmpl_id):
        """
        Busca automaticamente as variantes e subvariantes dos atributos do produto principal
        que utilizam este tecido.
        Retorna uma lista de dicionários com variant_id, variant_name, subvariant_name.
        """
        # Descoberta automatica de variantes de tecido a partir das BOMs onde
        # este tecido e usado como componente.
        variants = []
        
        # Encontra todos os produtos (variantes) deste tecido
        fabric_products = self.env['product.product'].search([
            ('product_tmpl_id', '=', fabric_product_tmpl_id)
        ])
        
        if not fabric_products:
            _logger.warning(f"Nenhum produto variante encontrado para o tecido com ID: {fabric_product_tmpl_id}")
            return variants

        # Encontra todas as linhas de BOM que usam este tecido
        bom_lines = self.env['mrp.bom.line'].search([
            ('product_id', 'in', fabric_products.ids)
        ])

        if not bom_lines:
            _logger.info(f"Nenhuma linha de BOM encontrada usando o tecido com ID: {fabric_product_tmpl_id}")
            return variants

        # Encontra os produtos principais (product.template) associados a essas BOMs
        main_product_tmpl_ids = bom_lines.mapped('bom_id.product_tmpl_id')
        
        for main_product_tmpl in main_product_tmpl_ids:
            # Busca atributos relacionados a FABRIC no produto principal
            for attribute_line in main_product_tmpl.attribute_line_ids:
                attribute = attribute_line.attribute_id
                
                # Verifica se é um atributo de tecido (contém FABRIC)
                if 'FABRIC' in attribute.name.upper():
                    # Extrai o número da variante do nome do atributo
                    match = re.search(r'FABRIC USED IN (\d+)', attribute.name, re.IGNORECASE)
                    if match:
                        variant_id = int(match.group(1))
                        variant_name = attribute.name
                        
                        # Para cada valor do atributo, cria uma subvariante
                        for value in attribute_line.value_ids:
                            variants.append({
                                'variant_id': variant_id,
                                'variant_name': variant_name,
                                'subvariant_name': value.name
                            })
        
        return variants
    
    def get_fabric_consumption(self, variant_keys, quantity):
        """
        Calcula o consumo total de tecido para um conjunto de subvariantes e uma quantidade.
        """
        self.ensure_one()
        total_consumption = 0.0
        
        if not variant_keys:
            return 0.0
        
        # Verifica se há uma subvariante "Total" e usa apenas ela se existir
        # Prioridade de negocio:
        # quando existe "Total", esse valor substitui somatorio de subpartes.
        total_key = next((key for key in variant_keys if 'total' in key.lower()), None)
        if total_key:
            # Extrai informações da chave
            variant_info = self._parse_variant_key(total_key)
            if variant_info:
                fabric_variant = self.env['fabric.variant'].search([
                    ('product_tmpl_id', '=', self.id),
                    ('variant_id', '=', variant_info['variant_id']),
                    ('subvariant_name', '=', variant_info['subvariant_name'])
                ], limit=1)
                
                if fabric_variant:
                    consumption = fabric_variant.get_consumption_for_quantity(quantity)
                    _logger.info(f"Usando consumo total para {total_key}: {consumption}m")
                    return consumption
            return 0.0
        
        # Caso contrário, soma o consumo de todas as subvariantes
        for key in variant_keys:
            variant_info = self._parse_variant_key(key)
            if variant_info:
                fabric_variant = self.env['fabric.variant'].search([
                    ('product_tmpl_id', '=', self.id),
                    ('variant_id', '=', variant_info['variant_id']),
                    ('subvariant_name', '=', variant_info['subvariant_name'])
                ], limit=1)
                
                if fabric_variant:
                    consumption = fabric_variant.get_consumption_for_quantity(quantity)
                    total_consumption += consumption
                    _logger.info(f"Adicionando consumo para {key}: {consumption}m")
        
        _logger.info(f"Consumo total calculado: {total_consumption}m")
        return total_consumption
    
    def _parse_variant_key(self, key):
        """
        Extrai informações de uma chave de variante.
        Formato esperado: "FABRIC USED IN X: Subvariante"
        """
        match = re.match(r'FABRIC USED IN (\d+):\s*(.+)', key, re.IGNORECASE)
        if match:
            return {
                'variant_id': int(match.group(1)),
                'subvariant_name': match.group(2).strip()
            }
        return None
        
        
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_custom_attribute_value_ids')
    def _check_fabric_total_combination(self):
        self.ensure_one()
        # Guard-rail de consistencia:
        # evita combinar "Total" com subvariantes detalhadas no mesmo conjunto.

        # Define os termos esperados e seus padrões de extração
        # Cada entrada é: 'TERMO_CHAVE': {'regex_pattern': regex_pattern, 'is_fabric': True/False}
        # Para termos FABRIC, o regex deve capturar o número do FABRIC, subvariante e label.
        # Para outros termos, o regex deve capturar o valor.
        term_definitions = {
            'FABRIC USED IN': {
                'regex_pattern': r'FABRIC USED IN (\d+)',
                'is_fabric': True
            },
            'ACABAMENTO': {
                'regex_pattern': r'ACABAMENTO:\s*(.*)',
                'is_fabric': False
            },
            'ACRÍLICO': {
                'regex_pattern': r'ACRÍLICO:\s*(.*)',
                'is_fabric': False
            },
            'ALTURA ASSENTO': {
                'regex_pattern': r'ALTURA ASSENTO:\s*(.*)',
                'is_fabric': False
            },
            'BASE': {
                'regex_pattern': r'BASE:\s*(.*)',
                'is_fabric': False
            },
            'BOTTOM': {
                'regex_pattern': r'BOTTOM:\s*(.*)',
                'is_fabric': False
            },
            'CASCO': {
                'regex_pattern': r'CASCO:\s*(.*)',
                'is_fabric': False
            },
            'COR': {
                'regex_pattern': r'COR:\s*(.*)',
                'is_fabric': False
            },
            'COSTA': {
                'regex_pattern': r'COSTA:\s*(.*)',
                'is_fabric': False
            },
            'DECORATIVAS': {
                'regex_pattern': r'DECORATIVAS:\s*(.*)',
                'is_fabric': False
            },
            'DIMENSIONS': {
                'regex_pattern': r'DIMENSIONS:\s*(.*)',
                'is_fabric': False
            },
            'ESPELHO': {
                'regex_pattern': r'ESPELHO:\s*(.*)',
                'is_fabric': False
            },
            'ESTRUTURA': {
                'regex_pattern': r'ESTRUTURA:\s*(.*)',
                'is_fabric': False
            },
            'EXTERIOR': {
                'regex_pattern': r'EXTERIOR:\s*(.*)',
                'is_fabric': False
            },
            'FABRIC': {
                'regex_pattern': r'FABRIC:\s*(.*)',
                'is_fabric': False
            },
            'FERROS INTERIORES': {
                'regex_pattern': r'FERROS INTERIORES:\s*(.*)',
                'is_fabric': False
            },
            'HANDLES': {
                'regex_pattern': r'HANDLES:\s*(.*)',
                'is_fabric': False
            },
            'INTERIOR': {
                'regex_pattern': r'INTERIOR:\s*(.*)',
                'is_fabric': False
            },
            'METAL': {
                'regex_pattern': r'METAL:\s*(.*)',
                'is_fabric': False
            },
            'MEDIDA': {
                'regex_pattern': r'MEDIDA:\s*(.*)',
                'is_fabric': False
            },
            'MÁRMORE': {
                'regex_pattern': r'MÁRMORE:\s*(.*)',
                'is_fabric': False
            },
            'POLIMENTO': {
                'regex_pattern': r'POLIMENTO:\s*(.*)',
                'is_fabric': False
            },
            'PORTA': {
                'regex_pattern': r'PORTA:\s*(.*)',
                'is_fabric': False
            },
            'PÉS': {
                'regex_pattern': r'PÉS:\s*(.*)',
                'is_fabric': False
            },
            'SUPORTES': {
                'regex_pattern': r'SUPORTES:\s*(.*)',
                'is_fabric': False
            },
            'TOP': {
                'regex_pattern': r'TOP:\s*(.*)',
                'is_fabric': False
            },
            'VENEER': {
                'regex_pattern': r'VENEER:\s*(.*)',
                'is_fabric': False
            },
            'VIDRO': {
                'regex_pattern': r'VIDRO:\s*(.*)',
                'is_fabric': False
            },
            'WOOD': {
                'regex_pattern': r'WOOD:\s*(.*)',
                'is_fabric': False
            },
            'FABRIC 1': {
                'regex_pattern': r'FABRIC 1:\s*(.*)',
                'is_fabric': False # Tratado como um termo geral, não como FABRIC USED IN
            },
            'FABRIC 2': {
                'regex_pattern': r'FABRIC 2:\s*(.*)',
                'is_fabric': False
            },
            'FABRIC 3': {
                'regex_pattern': r'FABRIC 3:\s*(.*)',
                'is_fabric': False
            },
        }

        extracted_terms = {} # Para armazenar todos os termos extraídos

        for attr_value in self.product_custom_attribute_value_ids:
            attr_name = attr_value.custom_product_template_attribute_value_id.attribute_id.name
            value_name = attr_value.custom_product_template_attribute_value_id.name

            for term_key, definition in term_definitions.items():
                if attr_name.startswith(term_key):
                    if definition['is_fabric']:
                        try:
                            fabric_num = int(attr_name.split(term_key)[1].strip())
                        except ValueError:
                            continue

                        parts = value_name.split(":")
                        if len(parts) == 2:
                            subvariant = parts[0].strip()
                            label = parts[1].strip()
                        else:
                            subvariant = value_name.strip()
                            label = ""
                        extracted_terms[f'FABRIC USED IN {fabric_num}'] = {'subvariant': subvariant, 'label': label}
                    else:
                        # Para outros termos, apenas armazena o valor
                        extracted_terms[term_key] = value_name.strip()
                    break # Termo encontrado, passa para o próximo attr_value

        total_found = False
        errors = []

        # Lógica de validação para FABRIC USED IN termos
        fabric_used_in_terms = {k: v for k, v in extracted_terms.items() if k.startswith('FABRIC USED IN')}
        sorted_fabric_used_in_terms = sorted(fabric_used_in_terms.items(), key=lambda item: int(item[0].split(' ')[-1]))

        for term_name, data in sorted_fabric_used_in_terms:
            subvariant_clean = data['subvariant'].lower()
            label_clean = data['label'].lower()
            fabric_id = int(term_name.split(' ')[-1])

            if subvariant_clean == "total":
                if total_found:
                    errors.append(f"Subvariante 'Total' usada mais de uma vez ({term_name})")
                total_found = True
                continue

            if total_found:
                if subvariant_clean != "nenhum":
                    errors.append(f"{term_name}: Subvariante inválida com 'Total' → esperado: 'Nenhum'")
                if label_clean not in ("", "mesmo"):
                    errors.append(f"{term_name}: Descrição inválida com 'Total' → esperado: 'Mesmo' ou vazio")

        if errors:
            raise ValidationError("Erro na configuração de tecido:\n" + "\n".join(errors))
            
            
            
