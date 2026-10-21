# -*- coding: utf-8 -*-
"""Ajustes aos snippets dinâmicos de produto do website.

Resumo (ver o __manifest__.py para detalhe):
- eleva o limite máximo de produtos que um snippet dinâmico pode mostrar (cap = 500);
- remove duplicados ao nível do template e esconde o produto que está a ser visto;
- mantém templates (sem converter para variante) nos snippets "Alternative/Related";
- resolve a lista de preços ativa de forma defensiva, compatível com este build do Odoo.
"""
from ast import literal_eval
import logging

from odoo import _, api, models
from odoo.exceptions import MissingError, ValidationError
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class WebsiteSnippetFilter(models.Model):
    _inherit = "website.snippet.filter"

    # Limite máximo absoluto de registos por snippet (o standard é bastante mais baixo).
    _dynamic_snippet_limit_cap = 500

    # -------------------------------------------------------------------------
    # Config
    # -------------------------------------------------------------------------

    def _get_dynamic_snippet_limit_cap(self):
        """Return the absolute maximum number of records a snippet can fetch."""
        return self._dynamic_snippet_limit_cap

    @api.constrains("limit")
    def _check_limit(self):
        """Allow a higher record limit for dynamic snippets."""
        for record in self:
            cap = record._get_dynamic_snippet_limit_cap()
            if not 0 < record.limit <= cap:
                raise ValidationError(_("The limit must be between 1 and %s.") % cap)

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _context_current_product_tmpl_id(self):
        """Try to extract current product template id from context."""
        ctx = self.env.context or {}
        for key in ("product_template_id", "product_tmpl_id", "product_template"):
            val = ctx.get(key)
            if val:
                try:
                    return int(val)
                except Exception:
                    return None
        return None

    def _active_website(self):
        """Return the current website record (sudoed, safe)."""
        try:
            return self.env["website"].sudo().get_current_website()
        except Exception:
            # Very defensive fallback: an empty browse that .exists() == False
            return self.env["website"].sudo().browse(False)

    def _get_active_pricelist(self):
        """
        Resolve the active pricelist WITHOUT calling website.get_current_pricelist()
        (method not present in this build). Order of preference:
          1) context['pricelist'] (set by website_sale)
          2) website.pricelist_id
          3) None (caller must handle fallback)
        """
        pl_id = (self.env.context or {}).get("pricelist")
        if pl_id:
            pl = self.env["product.pricelist"].sudo().browse(pl_id)
            if pl.exists():
                return pl
        website = self._active_website()
        if website and website.exists():
            pl = getattr(website.sudo(), "pricelist_id", False)
            if pl and pl.exists():
                return pl
        return None

    def _dedupe_to_templates(self, records, desired_limit):
        """Order-preserving dedupe to product.template, skipping current product."""
        if not records:
            return records

        model_name = records._name
        if model_name not in ("product.product", "product.template"):
            return records[:desired_limit]

        tmpl_model = self.env["product.template"]
        current_tmpl_id = self._context_current_product_tmpl_id()
        seen = set()
        tmpl_ids = []

        _logger.info(
            "[SnippetFilter] START dedupe for %s records (model=%s, desired_limit=%s)",
            len(records), model_name, desired_limit
        )

        for rec in records:
            tmpl = rec.product_tmpl_id if rec._name == "product.product" else rec
            if not tmpl:
                continue
            tid = tmpl.id
            if not tid:
                continue
            if current_tmpl_id and tid == current_tmpl_id:
                _logger.debug("[SnippetFilter] Skipping current product template id=%s", tid)
                continue
            if tid in seen:
                continue
            seen.add(tid)
            tmpl_ids.append(tid)
            if len(tmpl_ids) >= desired_limit:
                break

        result = tmpl_model.browse(tmpl_ids)
        _logger.info(
            "[SnippetFilter] END dedupe: %s unique templates kept (of %s fetched)",
            len(result), len(records)
        )
        return result

    # -------------------------------------------------------------------------
    # Main hook
    # -------------------------------------------------------------------------

    def _prepare_values(self, limit=None, search_domain=None):
        """Gets the data and returns it in the right format for render."""
        self.ensure_one()

        cap = self._get_dynamic_snippet_limit_cap()
        baseline = min(16, cap)

        if limit:
            try:
                requested = int(limit)
            except (TypeError, ValueError):
                requested = 0
            limit = min(cap, max(baseline, requested))
        else:
            record_limit = min(self.limit or 0, cap) if self.limit else 0
            limit = max(record_limit, baseline)

        _logger.info(
            "[SnippetFilter] _prepare_values called for filter %s (limit=%s, cap=%s, baseline=%s)",
            self.display_name, limit, cap, baseline
        )

        # ---------------------------------------------------------------------
        # Case 1: Domain-based filter (ir.filters)
        # ---------------------------------------------------------------------
        if self.filter_id:
            filter_sudo = self.filter_id.sudo()
            model_name = filter_sudo.model_id
            domain = filter_sudo._get_eval_domain()

            # Add website/company/published filters
            if "website_id" in self.env[model_name]:
                domain = expression.AND([domain, self.env["website"].get_current_website().website_domain()])
            if "company_id" in self.env[model_name]:
                website = self.env["website"].get_current_website()
                domain = expression.AND([domain, [("company_id", "in", [False, website.company_id.id])]])
            if "is_published" in self.env[model_name]:
                domain = expression.AND([domain, [("is_published", "=", True)]])
            if search_domain:
                domain = expression.AND([domain, search_domain])

            try:
                overfetch_limit = min(cap, max(limit * 3, limit, baseline))
                _logger.info(
                    "[SnippetFilter] Searching %s (filter_id=%s) domain=%s limit=%s overfetch_limit=%s",
                    model_name, self.filter_id.id, domain, limit, overfetch_limit,
                )

                records = (
                    self.env[model_name]
                    .with_context(**literal_eval(filter_sudo.context))
                    .search(domain, order=",".join(literal_eval(filter_sudo.sort)) or None, limit=overfetch_limit)
                )

                _logger.info("[SnippetFilter] Search returned %s raw records", len(records))
                records = self._dedupe_to_templates(records, desired_limit=limit)

                # ✅ Do NOT convert to variants when filter is “Alternative/Related”
                filter_name = (self.name or "").strip().lower()
                if "alternative" in filter_name or "related" in filter_name:
                    _logger.info("[SnippetFilter] Keeping templates for Alternative/Related products snippet.")
                else:
                    if records and records._name == "product.template":
                        _logger.info("[SnippetFilter] Converting %s templates to variants", len(records))
                        variant_ids = records.mapped("product_variant_id").ids
                        records = self.env["product.product"].browse(variant_ids)

                _logger.info("[SnippetFilter] %s records after normalization & dedupe", len(records))
                result = self._filter_records_to_values(records)
                _logger.info("[SnippetFilter] Returning %s final value dicts to renderer", len(result))
                return result

            except MissingError:
                _logger.warning(
                    "The provided domain %s in 'ir.filters' generated a MissingError in '%s'",
                    domain, self._name
                )
                return []

        # ---------------------------------------------------------------------
        # Case 2: Action Server (ir.actions.server)
        # ---------------------------------------------------------------------
        elif self.action_server_id:
            try:
                raw = (
                    self.action_server_id.with_context(
                        dynamic_filter=self, limit=limit, search_domain=search_domain
                    ).sudo().run() or []
                )

                _logger.info("[SnippetFilter] Action server returned %s raw values (%s type)",
                             len(raw) if hasattr(raw, "__len__") else "?", type(raw).__name__)

                if isinstance(raw, models.Model):
                    _logger.info("[SnippetFilter] Normalizing recordset from action server")
                    raw = self._dedupe_to_templates(raw, desired_limit=limit)

                    filter_name = (self.name or "").strip().lower()
                    if not ("alternative" in filter_name or "related" in filter_name):
                        if raw and raw._name == "product.template":
                            _logger.info("[SnippetFilter] Converting %s templates to variants", len(raw))
                            variant_ids = raw.mapped("product_variant_id").ids
                            raw = self.env["product.product"].browse(variant_ids)

                    return self._filter_records_to_values(raw)

                elif isinstance(raw, list) and raw and isinstance(raw[0], models.Model):
                    _logger.info("[SnippetFilter] Normalizing list of recordsets from action server")
                    all_ids = set()
                    for r in raw:
                        all_ids |= set(r.ids)
                    records = self.env["product.template"].browse(all_ids)
                    records = self._dedupe_to_templates(records, desired_limit=limit)

                    filter_name = (self.name or "").strip().lower()
                    if not ("alternative" in filter_name or "related" in filter_name):
                        if records and records._name == "product.template":
                            _logger.info("[SnippetFilter] Converting %s templates to variants", len(records))
                            variant_ids = records.mapped("product_variant_id").ids
                            records = self.env["product.product"].browse(variant_ids)

                    return self._filter_records_to_values(records)

                elif isinstance(raw, list) and raw and isinstance(raw[0], dict):
                    tmpl_ids = []
                    for entry in raw:
                        tid = (
                            entry.get("product_tmpl_id")
                            or entry.get("product_template_id")
                            or entry.get("id")
                        )
                        if tid:
                            tmpl_ids.append(int(tid))
                    tmpl_ids = list(dict.fromkeys(tmpl_ids))
                    _logger.info("[SnippetFilter] Found %s product template ids in dicts", len(tmpl_ids))
                    records = self.env["product.template"].browse(tmpl_ids)
                    records = self._dedupe_to_templates(records, desired_limit=limit)

                    filter_name = (self.name or "").strip().lower()
                    if not ("alternative" in filter_name or "related" in filter_name):
                        if records and records._name == "product.template":
                            _logger.info("[SnippetFilter] Converting %s templates to variants", len(records))
                            variant_ids = records.mapped("product_variant_id").ids
                            records = self.env["product.product"].browse(variant_ids)

                    return self._filter_records_to_values(records)

                _logger.info("[SnippetFilter] Using raw values directly (already dicts)")
                return raw

            except MissingError:
                _logger.warning(
                    "The provided domain %s in 'ir.actions.server' generated a MissingError in '%s'",
                    search_domain, self._name
                )
                return []

        # ---------------------------------------------------------------------
        # Fallback
        # ---------------------------------------------------------------------
        else:
            _logger.warning("[SnippetFilter] No filter_id or action_server_id found.")
            return []

    # -------------------------------------------------------------------------
    # Rendering helper override (fixed signature)
    # -------------------------------------------------------------------------

    def _filter_records_to_values(self, records, with_sample=False):
        """
        Override to gracefully handle product.template records
        for snippets like 'Alternative Products' that intentionally
        skip variant conversion.
        """
        if not records:
            return []

        model_name = records._name

        # Standard flow for product.product
        if model_name == "product.product":
            return super()._filter_records_to_values(records, with_sample)

        # Custom handling for product.template
        if model_name == "product.template":
            _logger.info(
                "[SnippetFilter] Rendering %s templates directly (no variant conversion)",
                len(records)
            )

            website = self._active_website()
            pricelist = self._get_active_pricelist()
            results = []

            for tmpl in records:
                price = None
                variant = tmpl.product_variant_id or tmpl.product_variant_ids[:1]

                # Prefer combination API if available
                if hasattr(tmpl, "_get_combination_info"):
                    try:
                        comb = tmpl._get_combination_info(
                            variant_id=variant,
                            add_qty=1,
                            pricelist=pricelist,  # may be None
                        )
                        price = comb.get("price")
                    except Exception as e:
                        _logger.debug(
                            "[SnippetFilter] _get_combination_info failed on tmpl %s: %s",
                            tmpl.id, e
                        )

                # Fallback to pricelist or list_price
                if price is None:
                    try:
                        if pricelist and variant:
                            price = pricelist._get_product_price(variant, 1.0, False)
                        else:
                            price = tmpl.list_price
                    except Exception:
                        price = tmpl.list_price

                values = {
                    "id": tmpl.id,
                    "name": tmpl.display_name,
                    "website_url": tmpl.website_url,
                    "image_url": f"/web/image/product.template/{tmpl.id}/image_512",
                    "is_published": bool(getattr(tmpl, "website_published", False)),
                    "price": price,
                    "record": tmpl,
                }
                results.append(values)

            return results

        # Fallback: call base method
        return super()._filter_records_to_values(records, with_sample)

