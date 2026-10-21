# -*- coding: utf-8 -*-
from odoo import models
import logging

_logger = logging.getLogger(__name__)


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _run_manufacture(self, procurements):
        _logger.info("=== [PG DEBUG] _run_manufacture START ===")
        productions = self.env['mrp.production']

        for procurement, rule in procurements:
            _logger.info("=== [PG DEBUG] New procurement ===")
            _logger.info("[PG DEBUG] Procurement object: %s", procurement)

            try:
                # ---- Normalize procurement + values ----
                if isinstance(procurement, dict):
                    values = procurement.get('values') or {}
                    group = procurement.get('group_id') and self.env['procurement.group'].browse(procurement.get('group_id')) or False
                    product = self.env['product.product'].browse(procurement.get('product_id'))
                    product_qty = procurement.get('product_qty')
                    product_uom = self.env['uom.uom'].browse(procurement.get('product_uom'))
                    location_id = self.env['stock.location'].browse(procurement.get('location_id'))
                    name = procurement.get('name')
                    origin = procurement.get('origin')
                    company_id = procurement.get('company_id') and self.env['res.company'].browse(procurement.get('company_id')) or self.env.company
                else:
                    values = getattr(procurement, 'values', {}) or {}
                    # IMPORTANT: in your flow, group is inside values['group_id']
                    group = getattr(procurement, 'group_id', False) or values.get('group_id') or False
                    product = procurement.product_id
                    product_qty = procurement.product_qty
                    product_uom = procurement.product_uom
                    location_id = procurement.location_id
                    name = procurement.name
                    origin = procurement.origin
                    company_id = procurement.company_id

                _logger.info("[PG DEBUG] Raw values keys: %s", list(values.keys()) if isinstance(values, dict) else values)
                _logger.info("[PG DEBUG] Group resolved to: %s", group)

                # ---- BOM + base MO vals (standard) ----
                bom = rule._get_matching_bom(product_id=product, company_id=company_id, values=values)
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
                production_vals['state'] = 'draft'

                # ---- Ensure procurement group passes (your earlier fix) ----
                if group and 'procurement_group_id' in self.env['mrp.production']._fields:
                    # group may be a record or a falsy/other object
                    if hasattr(group, "id"):
                        production_vals['procurement_group_id'] = group.id
                        _logger.info("[PG DEBUG] Set production_vals.procurement_group_id=%s", group.id)
                    else:
                        _logger.warning("[PG DEBUG] Group is not a recordset (type=%s): %s", type(group), group)

                # ---- Analytics handling ----
                if 'analytic_distribution' in self.env['mrp.production']._fields:

                    # 1) If values already carry analytic_distribution, normalize it
                    ad = None
                    if isinstance(values, dict) and values.get('analytic_distribution'):
                        ad = values.get('analytic_distribution')
                        _logger.info("[PG DEBUG] Found values['analytic_distribution']=%s", ad)

                    # 2) If not, try to build from SO analytic_account_id via group.sale_id
                    if not ad and group and hasattr(group, "_fields") and 'sale_id' in group._fields and group.sale_id and group.sale_id.analytic_account_id:
                        aa = group.sale_id.analytic_account_id
                        ad = {str(aa.id): 100.0}
                        _logger.info("[PG DEBUG] Built analytic_distribution from SO analytic_account_id=%s => %s", aa.id, ad)

                    # 3) Normalize dict keys to strings and values to floats (CRITICAL)
                    if isinstance(ad, dict):
                        normalized = {}
                        for k, v in ad.items():
                            try:
                                normalized[str(int(k))] = float(v)
                            except Exception:
                                normalized[str(k)] = float(v) if v is not None else 0.0
                        production_vals['analytic_distribution'] = normalized
                        _logger.info("[PG DEBUG] ✅ Normalized analytic_distribution=%s", normalized)
                    else:
                        _logger.warning("[PG DEBUG] ❌ No analytic_distribution resolved (ad=%s)", ad)

                _logger.info("[PG DEBUG] FINAL production_vals['analytic_distribution']=%s", production_vals.get('analytic_distribution'))
                _logger.info("[PG DEBUG] FINAL production_vals.procurement_group_id=%s", production_vals.get('procurement_group_id'))

                # ---- Create MO ----
                mo = self.env['mrp.production'].create(production_vals)
                productions |= mo
                
                # --- [PG DEBUG] Post-create analytic_distribution verification/fallback ---
                expected_ad = production_vals.get('analytic_distribution')
                _logger.info("[PG DEBUG] Post-create check | expected analytic_distribution=%s", expected_ad)
                _logger.info("[PG DEBUG] Post-create check | mo.analytic_distribution=%s", mo.analytic_distribution)

                if expected_ad and not mo.analytic_distribution:
                    # Ensure keys are strings (widget/storage expects string keys)
                    normalized = {}
                    if isinstance(expected_ad, dict):
                        for k, v in expected_ad.items():
                            try:
                                normalized[str(int(k))] = float(v)
                            except Exception:
                                normalized[str(k)] = float(v) if v is not None else 0.0

                    _logger.warning(
                        "[PG DEBUG] ⚠️ MO lost analytic_distribution during create. Forcing write now. normalized=%s",
                        normalized
                    )
                    try:
                        mo.sudo().write({'analytic_distribution': normalized})
                        _logger.info("[PG DEBUG] ✅ Forced write done. mo.analytic_distribution=%s", mo.analytic_distribution)
                    except Exception as e:
                        _logger.exception("[PG DEBUG] ❌ Failed to force-write analytic_distribution: %s", e)
                # ------------------------------------------------------------------------

                _logger.info("[PG DEBUG] 🏭 MO CREATED ID=%s NAME=%s", mo.id, mo.name)
                _logger.info("[PG DEBUG] MO.analytic_distribution AFTER CREATE: %s", mo.analytic_distribution)
                _logger.info("[PG DEBUG] MO.procurement_group_id AFTER CREATE: %s", mo.procurement_group_id.id if mo.procurement_group_id else False)

            except Exception as e:
                _logger.exception("[PG DEBUG] ❌ ERROR in _run_manufacture: %s", e)
                raise

        _logger.info("=== [PG DEBUG] _run_manufacture END ===")
        return productions
