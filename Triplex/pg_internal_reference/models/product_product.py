# -*- coding: utf-8 -*-
"""Atribuição automática da referência interna (default_code) das variantes.

Formato "<BASE>-<NNNNN>", em que BASE vem da 1ª variante com código do template e NNNNN
é um contador a 5 dígitos. Ver o __manifest__.py para o guia completo.
"""
from odoo import models, api
import logging

_logger = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def create(self, vals):
        """Após criar a variante, atribui-lhe um default_code se ainda não tiver."""
        product = super(ProductProduct, self).create(vals)

        try:
            # Só atua quando a variante foi criada sem referência interna.
            if not product.default_code:
                # Código base = referência da 1ª variante (mais antiga) que já tenha código.
                first_variant = self.search([
                    ('product_tmpl_id', '=', product.product_tmpl_id.id),
                    ('default_code', '!=', False)
                ], limit=1, order="id asc")

                if first_variant:
                    # Base = parte antes do primeiro "-" (ex.: "CAD" em "CAD-00001").
                    base_code = first_variant.default_code.split('-')[0]

                    # Find existing codes for this template
                    existing_codes = self.search([
                        ('product_tmpl_id', '=', product.product_tmpl_id.id),
                        ('default_code', 'like', f"{base_code}-%")
                    ]).mapped('default_code')

                    # Extract counters from existing codes
                    counters = [
                        int(code.split('-')[-1]) for code in existing_codes
                        if code.split('-')[-1].isdigit()
                    ]

                    # Próximo número = maior contador existente + 1 (deixa "buracos" se houver apagados).
                    next_counter = max(counters, default=0) + 1

                    # Referência final com contador a 5 dígitos (ex.: "CAD-00002").
                    product.default_code = f"{base_code}-{next_counter:05d}"
                    _logger.info(f"Assigned default_code {product.default_code} to variant {product.id}")
                else:
                    _logger.warning(f"No base default_code found for product template {product.product_tmpl_id.id}. Skipping default_code assignment.")

            # Trigger assigning default codes to all existing variants of the same template
            product.product_tmpl_id.product_variant_ids.assign_default_codes_to_all_variants()
        except Exception as e:
            _logger.error(f"Error assigning default_code to product {product.id}: {e}")

        return product

    def assign_default_codes_to_all_variants(self):
        """Preenche a referência de todas as variantes (do template) que ainda não a têm.

        Útil para produtos antigos ou criados antes da instalação deste módulo.
        """
        for template in self.mapped('product_tmpl_id'):
            # Search for the first variant's default_code as the base code
            first_variant = template.product_variant_ids.filtered(lambda v: v.default_code).sorted('id')
            if first_variant:
                base_code = first_variant[0].default_code.split('-')[0]

                # Find existing codes for this template
                existing_codes = template.product_variant_ids.mapped('default_code')
                counters = [
                    int(code.split('-')[-1]) for code in existing_codes
                    if code and code.split('-')[-1].isdigit()
                ]
                next_counter = max(counters, default=0) + 1

                for variant in template.product_variant_ids:
                    if not variant.default_code:
                        variant.default_code = f"{base_code}-{next_counter:05d}"
                        _logger.info(f"Assigned default_code {variant.default_code} to variant {variant.id}")
                        next_counter += 1
            else:
                _logger.warning(f"No base default_code found for product template {template.id}. Skipping assignment for variants.")

