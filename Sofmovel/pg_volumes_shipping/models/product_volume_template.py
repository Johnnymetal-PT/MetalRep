"""Quantidade de volumes e peso por volume no template + indices em variantes.

Pertence ao modulo `pg_volumes_shipping`. Adiciona dois campos ao template
(volume_qty, peso_cada_volume com separador "/") e garante que as variantes
recebem `x_studio_referncia_interna` e `x_studio_cdigo_de_barras` (Studio,
store, index).
"""
from odoo import models, api, fields, _

class setVolumes(models.Model):
    """Campos de volume/peso na template e propagacao para variantes."""

    _inherit = 'product.template'

    volume_qty = fields.Float(string='Quantidade Volume', store=True)
    peso_cada_volume = fields.Char(string="Peso Cada Volume", help="Weights for each volume", default='0.0')
    
    @api.onchange('default_code', 'barcode')
    def _onchange_propagate_to_variants(self):
        # Quando o utilizador mexe em default_code ou barcode no template,
        # propaga para as variantes nos campos Studio (x_studio_*). So
        # corre em UI (onchange); para criacoes programaticas em massa
        # confiar nos imports respeitarem os campos.
        if self.product_variant_ids:
            for variant in self.product_variant_ids:
                variant_internal_ref = self.default_code or ''
                variant_ean_code = self.barcode or ''
                variant.write({
                    'x_studio_referncia_interna': variant_internal_ref,
                    'x_studio_cdigo_de_barras': variant_ean_code
                })
    
class ProductProduct(models.Model):
    """Forca store + index nos campos Studio de referencia/barcode."""

    _inherit = 'product.product'

    x_studio_referncia_interna = fields.Char(
        store=True,  # Make the field stored
        readonly=False,  # Allow editing
        index=True  # Index for performance
    )
    x_studio_cdigo_de_barras = fields.Char(
        store=True,
        readonly=False,
        index=True
    )
