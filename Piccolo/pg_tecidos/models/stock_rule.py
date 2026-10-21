"""Override do _run_manufacture: MO sempre em ``draft``.

O standard cria a MO em ``confirmed``; em Piccolo queremos draft
para o operador validar/ajustar antes de bloquear stock e disparar
compras.
"""
from odoo import models, api, fields
import logging

_logger = logging.getLogger(__name__)


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _run_manufacture(self, procurements):
        for procurement, rule in procurements:
            # ``procurement.product_id`` pode chegar como int em algumas
            # versoes do trigger - normalizar para recordset.
            product = procurement.product_id if isinstance(procurement.product_id, models.Model) else self.env['product.product'].browse(procurement.product_id)
            product_qty = procurement.product_qty
            product_uom = procurement.product_uom
            location_id = procurement.location_id
            name = procurement.name
            origin = procurement.origin
            company_id = procurement.company_id
            values = procurement.values if isinstance(procurement.values, dict) else {}
            values.setdefault('date_planned', fields.Datetime.now())

            bom = self.env['mrp.bom'].search([
                ('product_tmpl_id', '=', product.product_tmpl_id.id),
                ('company_id', '=', company_id.id),
            ], limit=1)

            if not bom:
                raise ValueError(f"No Bill of Materials found for product template {product.product_tmpl_id.name}")

            try:
                production_vals = rule._prepare_mo_vals(
                    product_id=product,
                    product_qty=product_qty,
                    product_uom=product_uom,
                    location_id=location_id,
                    name=name,
                    origin=origin,
                    company_id=company_id,
                    values=values,
                    bom=bom,
                )
                # FORCA estado draft (default seria 'confirmed').
                production_vals['state'] = 'draft'
                mo = self.env['mrp.production'].create(production_vals)

                mo.message_post(
                    body="Manufacturing Order created from origin: {}".format(procurement.origin),
                    subtype_id=self.env.ref('mail.mt_note').id,
                )

                # Ligar a MO ao mesmo procurement group para que o
                # ``pg_sale_purchase_link`` consiga reconstruir o link.
                if hasattr(procurement, 'group_id') and procurement.group_id:
                    procurement.group_id.mrp_production_ids = [(4, mo.id)]

            except (TypeError, AttributeError) as e:
                _logger.error("Error in _run_manufacture: %s", e)
                raise
