"""Modelos auxiliares de "atributos textuais" do `pg_variant_upload`.

`custom.product.attribute` guarda combinacoes atributo+valor que NAO sao
variantes standard (sem `product.attribute.value`), tipicamente porque o XLSX
de importacao tinha texto livre na celula em vez de um price_extra numerico.

Tambem e reaproveitado pelo [[pg_custom_product_import_extension_2]] para
guardar valores de "Cor" textuais quando nao se quer criar variantes.
"""
from odoo import models, fields, api

class CustomProductAttribute(models.Model):
    """Atributo textual associado a um product.template (sem variante real)."""

    _name = 'custom.product.attribute'
    _description = 'Custom Product Attribute'

    # Atributo textual livre vindo do XLSX (sem product.attribute.value real).
    name = fields.Char('Attribute Name')
    product_id = fields.Many2one('product.template', string='Product', required=True)
    description = fields.Text('Description', required=True)
    sequence = fields.Integer('Sequence', default=1)
    

class CustomProductAttributeValue(models.Model):
    """[PONTO POR VALIDAR] Modelo declarado mas nao usado pelo fluxo de import."""

    _name = 'custom.product.attribute.value'
    _description = 'Custom Product Attribute Value'

    # Modelo declarado para extensoes futuras; fluxo base nao persiste aqui.
    name = fields.Char('Variant Name', required=True)
    attribute_id = fields.Many2one('custom.product.attribute', string='Attribute', required=True)
    price = fields.Float('Price')

