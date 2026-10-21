"""Recalcula `x_variant_sale_price` por variante segundo a pricelist.

Pertence ao modulo `pg_update_variant_prices`. Disparado manualmente; nao tem
cron. Nao toca em `lst_price` - escreve apenas no campo custom.
"""
import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    """Adiciona `x_variant_sale_price` para guardar o preco da pricelist."""

    _inherit = 'product.product'

    x_variant_sale_price = fields.Float(string="Custom Variant Sale Price")

class ProductPricelist(models.Model):
    """Pricelist com accao manual para recalcular precos por variante."""

    _inherit = 'product.pricelist'

    def action_update_variant_prices(self):
        """Itera items por variante e grava preco em `x_variant_sale_price`."""
        for pricelist in self:
            _logger.info("🔁 Processing Pricelist: %s (ID: %s)", pricelist.name, pricelist.id)

            # Apenas regras aplicadas diretamente a variante (nao categoria/global).
            items = pricelist.item_ids.filtered(lambda i: i.applied_on == '0_product_variant' and i.product_id)
            _logger.info("📦 Found %d variant-level items to update", len(items))

            for item in items:
                variant = item.product_id
                _logger.info("🔍 Updating variant: %s (ID: %s)", variant.display_name, variant.id)

                try:
                    price = pricelist._get_product_price(
                        product=variant,
                        quantity=1.0,
                        partner=None
                    )
                    _logger.info("💸 Computed price for %s: %s", variant.display_name, price)

                    if price != variant.lst_price:
                        # Nao mexe no `lst_price`: grava apenas no campo custom.
                        _logger.info("✏️ Writing lst_price from %s to %s", variant.lst_price, price)
                        variant.write({'x_variant_sale_price': price})
                    else:
                        _logger.info("ℹ️ Price unchanged for %s", variant.display_name)

                except Exception as e:
                    _logger.error("❌ Error computing price for variant %s: %s", variant.display_name, str(e))

            _logger.info("✅ Finished updating variants for pricelist: %s", pricelist.name)
