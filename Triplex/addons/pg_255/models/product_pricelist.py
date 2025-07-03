from odoo import models, api, fields
import logging

_logger = logging.getLogger(__name__)


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    def _compute_price_rule(self, products, quantity, currency=None, uom=None, date=False, compute_price=True, **kwargs):
        if not isinstance(products, models.BaseModel):
            _logger.warning("Products are not a recordset. Converting to recordset.")
            products = self.env['product.product'].browse([p.id for p in products])

        _logger.info(f"Computing price rule for pricelist: {self.name}")
        results = super()._compute_price_rule(
            products, quantity, currency=currency, uom=uom, date=date, compute_price=compute_price, **kwargs
        )

        if self.x_studio_255 or self.x_studio_maison_dore:
            mode = "255" if self.x_studio_255 else "Maison Dorée"
            _logger.info(f"{mode} checkbox is active for pricelist {self.name}")

            for product in products:
                try:
                    if product.id not in results:
                        _logger.warning(f"Product {product.display_name} not found in results")
                        continue

                    # Fetch base price info
                    lst_price = product.lst_price
                    tmpl_list_price = product.product_tmpl_id.list_price
                    price_extra = product.price_extra or 0.0
                    base_price = lst_price or (tmpl_list_price or 0.0) + price_extra

                    # Compute 255 price first
                    price_255 = (base_price / 2) * 2.55
                    _logger.debug(f"255 price for {product.display_name}: {price_255}")

                    if self.x_studio_255:
                        final_price = price_255
                    elif self.x_studio_maison_dore:
                        final_price = (((price_255 * 0.5) * 0.7) * 11)
                        _logger.debug(f"Maison Dorée price from 255 price for {product.display_name}: {final_price}")

                    results[product.id] = (final_price, results[product.id][1])
                    _logger.info(f"{mode} - Final computed price for {product.display_name}: {final_price}")

                except Exception as e:
                    _logger.error(f"Error processing product {product.display_name}: {e}", exc_info=True)

        return results


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('product_id', 'product_uom_qty', 'order_id.pricelist_id', 'order_id.partner_id')
    def _compute_price_unit(self):
        super()._compute_price_unit()

        for line in self:
            try:
                pricelist = line.order_id.pricelist_id
                if not pricelist:
                    continue

                mode = None
                if pricelist.x_studio_255:
                    mode = "255"
                elif pricelist.x_studio_maison_dore:
                    mode = "Maison Dorée"

                if mode:
                    _logger.info(f"Applying {mode} logic for SO Line ID: {line.id}, Product: {line.product_id.display_name}")

                    price_rule = pricelist._compute_price_rule(
                        line.product_id,
                        line.product_uom_qty,
                        currency=pricelist.currency_id,
                        uom=line.product_uom,
                        partner=line.order_id.partner_id
                    )
                    custom_price = price_rule.get(line.product_id.id, (0.0, None))[0]

                    if custom_price:
                        _logger.info(f"{mode} - Setting custom price_unit for {line.product_id.display_name}: {custom_price}")
                        line.price_unit = custom_price
                    else:
                        _logger.warning(f"{mode} - No custom price found for {line.product_id.display_name}")
            except Exception as e:
                _logger.error(f"Error updating price_unit for SO Line ID: {line.id}: {e}", exc_info=True)

