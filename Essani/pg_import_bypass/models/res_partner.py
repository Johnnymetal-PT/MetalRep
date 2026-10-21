# -*- coding: utf-8 -*-
"""Bypass controlado da validacao VAT apenas em importacoes ou por parametro temporario."""
import logging

from odoo import api, models


_logger = logging.getLogger(__name__)


SYSTEM_PARAM_KEY = "pg_import_bypass.disable_vat_check"


def _is_bypass_active(env):
    """Return True when VAT validation should be skipped.

    Three triggers, any one of which is enough:

    * ``env.context["import_file"]`` — set automatically by base_import.
    * ``env.context["no_vat_validation"]`` — native base_vat opt-out.
    * ``ir.config_parameter`` ``pg_import_bypass.disable_vat_check`` set to
      a truthy value (``1``/``true``/``yes``). This last one is a manual
      kill-switch — admin flips it on before a bulk import, runs the
      import, flips it back off. Works even when the wizard fails to
      propagate the context (which is what we saw with the Teste button).
    """
    ctx = env.context or {}
    if ctx.get("import_file") or ctx.get("no_vat_validation"):
        return True
    try:
        flag = env["ir.config_parameter"].sudo().get_param(SYSTEM_PARAM_KEY, "")
    except Exception:
        return False
    return str(flag).strip().lower() in ("1", "true", "yes", "on")


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def _run_vat_checks(self, country, vat, partner_name="", validation="error"):
        if _is_bypass_active(self.env):
            _logger.warning(
                "pg_import_bypass: skipping _run_vat_checks for %s "
                "(country=%s, import_file=%s, no_vat_validation=%s, sys_param=%s)",
                partner_name or "partner",
                country.code if country else "",
                self.env.context.get("import_file"),
                self.env.context.get("no_vat_validation"),
                self.env["ir.config_parameter"].sudo().get_param(SYSTEM_PARAM_KEY, ""),
            )
            # Odoo 19 raises on one-character VAT values before checking
            # no_vat_validation, so import bypass must avoid base_vat entirely.
            return vat, country.code if country else False
        return super()._run_vat_checks(
            country, vat, partner_name=partner_name, validation=validation
        )

    @api.model
    def _check_vat_number(self, country_code, vat_number):
        if _is_bypass_active(self.env):
            return True
        return super()._check_vat_number(country_code, vat_number)

    def check_vat(self):
        if _is_bypass_active(self.env):
            _logger.warning(
                "pg_import_bypass: skipping check_vat for %s record(s) "
                "(import_file=%s, no_vat_validation=%s, sys_param=%s)",
                len(self),
                self.env.context.get("import_file"),
                self.env.context.get("no_vat_validation"),
                self.env["ir.config_parameter"].sudo().get_param(SYSTEM_PARAM_KEY, ""),
            )
            return
        return super().check_vat()

    @api.model
    def _run_vat_test(self, vat_number, default_country, partner_is_company=True):
        if _is_bypass_active(self.env):
            if default_country and getattr(default_country, "code", None):
                return default_country.code.lower()
            return True
        return super()._run_vat_test(
            vat_number, default_country, partner_is_company=partner_is_company
        )

    @api.model
    def simple_vat_check(self, country_code, vat_number):
        if _is_bypass_active(self.env):
            return True
        return super().simple_vat_check(country_code, vat_number)
