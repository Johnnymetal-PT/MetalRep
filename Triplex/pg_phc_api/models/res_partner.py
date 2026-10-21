# -*- coding: utf-8 -*-
"""Sincronização de clientes (res.partner) com o PHC CSWeb via SOAP.

Ao gravar o parceiro, o conector chama o script PHC CriaCL (criar) ou UpdateCL (atualizar),
respeitando os limites de tamanho do PHC (PHC_LIMITS) e regras de NIF. Ver o __manifest__.py
para o guia completo. (NOTA: res_partner_old.py é uma versão antiga, não importada.)
"""
import json
import logging
import re
import xml.etree.ElementTree as ET

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

# Códigos dos scripts PHC chamados via SOAP: criar e atualizar cliente.
PHC_SCRIPT_CODE = "CriaCL"
PHC_SCRIPT_UPDATE_CODE = "UpdateCL"

# PHC message that means "VAT change is forbidden"
PHC_VAT_LOCK_MSG_SNIPPET = "não pode alterar o NIF"

# ✅ VAT duplicate exceptions (placeholders allowed)
VAT_DUPLICATE_EXCEPTIONS_RAW = {"999999990", "SEM NIF"}
VAT_DUPLICATE_EXCEPTIONS = {
    re.sub(r"\s+", "", str(x)).strip().upper() for x in VAT_DUPLICATE_EXCEPTIONS_RAW
}


class ResUsers(models.Model):
    _inherit = "res.users"

    x_studio_salesperson_id_1 = fields.Integer(
        string="Vendedor PHC (nº)",
        help="Número do vendedor no PHC (vendedornr). Usado para mapear parceiros (res.partner) ao user_id.",
        index=True,
    )


class ResPartner(models.Model):
    _inherit = "res.partner"

    PHC_LIMITS = {
        "vat": 20,
        "name": 55,
        "street": 55,
        "zip": 45,
        "phone": 45,
        "email": 100,
        "city": 43,
        "x_studio_country_code": 2,
        "x_studio_salesperson_id_1": 4,
        "property_payment_term_id": 55,
        "x_studio_tabela_precos": 1,
        "responsavel_interno": 30,  # keep field, but DO NOT send to PHC
        "ref": 20,
        "motivo_isencao": 3,  # e.g. M01
    }

    # -----------------------------
    # PHC toggle
    # -----------------------------
    is_phc_synced = fields.Boolean(
        string="PHC Synced",
        default=False,
        help="False = criar no PHC no próximo save. True = atualizar no PHC a cada save.",
    )

    phc_last_response = fields.Text(
        string="Última resposta PHC",
        readonly=True,
        help="Resposta bruta do serviço PHC (para debug).",
    )

    # -----------------------------
    # Fields
    # -----------------------------
    x_studio_country_code = fields.Char(
        string="Código País PHC",
        size=PHC_LIMITS["x_studio_country_code"],
        required=False,
        help="Código de país PHC (pncont). Ex: PT",
    )

    x_studio_salesperson_id_1 = fields.Integer(
        string="Vendedor PHC (nº)",
        required=False,
        help="Número do vendedor no PHC (vendedornr). Mapeia user_id via res.users.x_studio_salesperson_id_1.",
        index=True,
    )

    x_studio_salesperson_id = fields.Integer(
        string="Vendedor PHC old",
        required=False,
        help="Número do vendedor no PHC (vendedornr) old",
    )

    x_studio_tabela_precos = fields.Selection(
        selection=[("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5")],
        string="Tabela de Preços (PHC)",
        required=False,
        help="Tabela de preços PHC (tabprecost).",
    )

    responsavel_interno = fields.Char(
        string="Responsável Interno (PHC)",
        size=PHC_LIMITS["responsavel_interno"],
        required=False,
        help="Campo mantido por compatibilidade, mas NÃO é enviado para o PHC nesta BD.",
    )

    motivo_isencao = fields.Selection(
        selection=[
            ("M01", "M01 - Artigo 16.º, n.º 6 do CIVA"),
            ("M02", "M02 - Artigo 6.º do Decreto-Lei n.º 198/90, de 19 de junho"),
            ("M04", "M04 - Isento artigo 13.º do CIVA"),
            ("M05", "M05 - Isento artigo 14.º do CIVA"),
            ("M06", "M06 - Isento artigo 15.º do CIVA"),
            ("M07", "M07 - Isento artigo 9.º do CIVA"),
            ("M08", "M08 - IVA - autoliquidação"),
            ("M09", "M09 - IVA - não confere direito a dedução"),
            ("M10", "M10 - IVA - regime de isenção"),
            ("M11", "M11 - Regime particular do tabaco"),
            ("M12", "M12 - Regime da margem de lucro - Agências de viagens"),
            ("M13", "M13 - Regime da margem de lucro - Bens em segunda mão"),
            ("M14", "M14 - Regime da margem de lucro - Objetos de arte"),
            ("M15", "M15 - Regime da margem de lucro - Objetos de coleção e antiguidades"),
            ("M16", "M16 - Isento artigo 14.º do RITI"),
            ("M19", "M19 - Outras isenções - artigo 16.º do RITI"),
            ("M20", "M20 - IVA - regime forfetário"),
            ("M21", "M21 - IVA - regime da margem de lucro - bens em segunda mão"),
            ("M25", "M25 - IVA – regime especial de isenção - artigo 53.º"),
            ("M26", "M26 - IVA – regime especial de isenção - artigo 54.º"),
            ("M30", "M30 - IVA - regime especial de isenção - artigo 57.º"),
            ("M31", "M31 - IVA - regime especial de isenção - artigo 58.º"),
            ("M32", "M32 - IVA - regime especial de isenção - artigo 59.º"),
            ("M33", "M33 - IVA - regime especial de isenção - artigo 60.º"),
            ("M34", "M34 - IVA - regime especial de isenção - artigo 61.º"),
            ("M40", "M40 - IVA – regime particular do tabaco"),
            ("M41", "M41 - IVA – regime especial de isenção - artigo 1.º"),
            ("M42", "M42 - IVA – regime especial de isenção - artigo 5.º"),
            ("M43", "M43 - IVA - autoliquidação"),
            ("M44", "M44 - IVA – Regras específicas - artigo 6.º"),
            ("M45", "M45 - IVA – regime transfronteiriço de isenção"),
            ("M46", "M46 - IVA – e-TaxFree"),
            ("M99", "M99 - Não sujeito ou não tributado"),
        ],
        string="Motivo de Isenção",
        required=False,
        help="Enviado ao PHC como codmotisencao (apenas o código: M01, M02, ...).",
    )

    # --------------------------------------------------------------
    # Utils
    # --------------------------------------------------------------
    @staticmethod
    def _phc_trim(value, limit):
        if not value:
            return ""
        return str(value)[:limit]

    @staticmethod
    def _normalize_vat_generic(vat_value):
        """Generic VAT normalize: trim, remove spaces, uppercase."""
        if not vat_value:
            return ""
        return str(vat_value).strip().replace(" ", "").upper()

    def _is_pt_partner(self):
        """PT detection: country_id.code == PT OR x_studio_country_code == PT."""
        self.ensure_one()
        c1 = (self.country_id.code or "").strip().upper() if self.country_id else ""
        c2 = (self.x_studio_country_code or "").strip().upper()
        return c1 == "PT" or c2 == "PT"

    def _normalize_vat_pt_digits(self, vat_value):
        """
        For PT comparisons/storage:
        - If 'PT123456789' -> '123456789'
        - If '123456789' -> '123456789'
        - Else -> normalized generic
        """
        v = self._normalize_vat_generic(vat_value)
        if not v:
            return ""
        if v.startswith("PT") and re.fullmatch(r"PT\d{9}", v):
            return v[2:]
        return v

    def _get_user_by_phc_salesperson_nr(self, salesperson_nr):
        if not salesperson_nr:
            return self.env["res.users"]
        return self.env["res.users"].sudo().search(
            [("x_studio_salesperson_id_1", "=", int(salesperson_nr))],
            limit=1,
        )

    @staticmethod
    def _phc_extract_ref_from_run_code_result(run_code_result):
        if not run_code_result:
            return ""

        text = (run_code_result or "").strip()

        try:
            data = json.loads(text)
            if isinstance(data, list) and data:
                obj = data[0] if isinstance(data[0], dict) else None
                if obj and obj.get("Numero"):
                    return str(obj.get("Numero")).strip()
        except Exception:
            pass

        m = re.search(r'"Numero"\s*:\s*"?(?P<num>\d+)"?', text)
        if m:
            return m.group("num").strip()

        m2 = re.search(r"(\d+)\s*$", text)
        return m2.group(1) if m2 else ""

    @staticmethod
    def _phc_extract_message_from_run_code_result(run_code_result):
        if not run_code_result:
            return ""

        text = (run_code_result or "").strip()

        try:
            data = json.loads(text)
            if isinstance(data, list) and data and isinstance(data[0], dict):
                msg = data[0].get("Mensagem") or ""
                return str(msg).strip()
        except Exception:
            pass

        m = re.search(r'"Mensagem"\s*:\s*"(?P<msg>[^"]+)"', text)
        return m.group("msg").strip() if m else ""

    def _has_posted_customer_documents(self):
        self.ensure_one()
        Move = self.env["account.move"].sudo()
        cnt = Move.search_count(
            [
                ("partner_id", "=", self.id),
                ("state", "=", "posted"),
                ("move_type", "in", ("out_invoice", "out_refund")),
            ]
        )
        return cnt > 0

    # --------------------------------------------------------------
    # ✅ PT VAT format rule (9 digits only) except placeholders
    # --------------------------------------------------------------
    @api.constrains("vat", "country_id", "x_studio_country_code")
    def _check_pt_vat_format(self):
        for rec in self:
            if not rec.vat:
                continue

            vat_norm = rec._normalize_vat_generic(rec.vat)
            if not vat_norm:
                continue

            # Allow placeholders
            if vat_norm in VAT_DUPLICATE_EXCEPTIONS:
                continue

            # PT: must be exactly 9 digits (we also accept PT######### but convert in check_vat/write)
            if rec._is_pt_partner():
                digits = rec._normalize_vat_pt_digits(vat_norm)
                if not re.fullmatch(r"\d{9}", digits):
                    raise ValidationError(
                        _(
                            "Para clientes com país Portugal (PT), o NIF deve ter exatamente 9 dígitos "
                            "(ex: 123456789). Alternativamente pode usar o placeholder 'SEM NIF'."
                        )
                    )

    # --------------------------------------------------------------
    # ✅ Relax Odoo VAT validation for PT:
    # - Accept PT VAT without checksum
    # - Store only 9 digits for PT
    # - Allow placeholders (SEM NIF / 999999990)
    # --------------------------------------------------------------
    def check_vat(self):
        """
        Override Odoo VAT validation:
        - For PT partners (country_id=PT OR x_studio_country_code=PT):
            * allow '123456789' (9 digits)
            * if 'PT123456789' -> auto-convert to '123456789'
            * allow placeholders (SEM NIF / 999999990)
          WITHOUT checksum validation.
        - For other countries, keep default behavior.
        """
        # First, normalize PT values (strip PT prefix) and decide who to validate with super()
        to_super = self.env["res.partner"]  # empty recordset

        for partner in self:
            if not partner.vat:
                to_super |= partner
                continue

            vat_norm = partner._normalize_vat_generic(partner.vat)

            # placeholders: bypass super VAT validation
            if vat_norm in VAT_DUPLICATE_EXCEPTIONS:
                continue

            if partner._is_pt_partner():
                # if PT######### -> store digits only
                if re.fullmatch(r"PT\d{9}", vat_norm):
                    partner.vat = vat_norm[2:]
                    continue
                # if already 9 digits -> ok
                if re.fullmatch(r"\d{9}", vat_norm):
                    partner.vat = vat_norm
                    continue
                # anything else (PT partner but wrong format) -> let constraints raise, skip super
                continue

            # non-PT -> validate with default behavior
            to_super |= partner

        if to_super:
            return super(ResPartner, to_super).check_vat()
        return True

    # --------------------------------------------------------------
    # ✅ VAT uniqueness lock (with exceptions)
    # --------------------------------------------------------------
    @api.constrains("vat", "country_id", "x_studio_country_code")
    def _check_unique_vat(self):
        # Duplicate VAT should not block contact creation/update.
        # It is handled as a PHC sync blocker.
        return

        for rec in self:
            if not rec.vat:
                continue

            raw = rec._normalize_vat_generic(rec.vat)

            # Allow placeholder VATs
            if raw in VAT_DUPLICATE_EXCEPTIONS:
                continue

            # Normalize for PT comparison
            if rec._is_pt_partner():
                vat_norm = rec._normalize_vat_pt_digits(raw)
            else:
                vat_norm = raw

            if not vat_norm:
                continue

            others = self.env["res.partner"].sudo().search(
                [("id", "!=", rec.id), ("vat", "!=", False)]
            )
            for other in others:
                other_raw = rec._normalize_vat_generic(other.vat)

                # Ignore other placeholders too
                if other_raw in VAT_DUPLICATE_EXCEPTIONS:
                    continue

                # Normalize other according to its PT-ness (best-effort)
                if other._is_pt_partner():
                    other_norm = other._normalize_vat_pt_digits(other_raw)
                else:
                    other_norm = other_raw

                if other_norm == vat_norm:
                    raise ValidationError(
                        _(
                            "Não é possível gravar: o NIF/VAT '%s' já existe no contacto '%s' (ID %s)."
                        )
                        % (rec.vat, other.display_name, other.id)
                    )

    # --------------------------------------------------------------
    #  COHERENCE (incoming/outgoing)
    # --------------------------------------------------------------
    def _get_duplicate_vat_partner(self):
        self.ensure_one()
        if not self.vat:
            return self.env["res.partner"]

        raw = self._normalize_vat_generic(self.vat)
        if not raw or raw in VAT_DUPLICATE_EXCEPTIONS:
            return self.env["res.partner"]

        vat_norm = self._normalize_vat_pt_digits(raw) if self._is_pt_partner() else raw
        if not vat_norm:
            return self.env["res.partner"]

        # Contactos da mesma entidade comercial (a empresa e os seus subcontactos) herdam
        # o mesmo NIF por desenho do Odoo: não são duplicados.
        others = self.env["res.partner"].sudo().search([
            ("id", "!=", self.id),
            ("vat", "!=", False),
            ("commercial_partner_id", "!=", self.commercial_partner_id.id),
        ])
        for other in others:
            other_raw = self._normalize_vat_generic(other.vat)
            if not other_raw or other_raw in VAT_DUPLICATE_EXCEPTIONS:
                continue

            other_norm = (
                other._normalize_vat_pt_digits(other_raw) if other._is_pt_partner() else other_raw
            )
            if other_norm == vat_norm:
                return other

        return self.env["res.partner"]

    @staticmethod
    def _phc_company_uses_ofc22_ref(company):
        """Use x_studio_ref_ofc22 for Oficinna22; otherwise use standard ref."""
        if not company:
            return False
        token = re.sub(r"[^a-z0-9]", "", (company.name or "").lower())
        return any(name in token for name in ("ofc22", "oficina22", "oficinna22"))

    def _phc_get_effective_ref(self):
        self.ensure_one()
        if self._phc_company_uses_ofc22_ref(self.env.company) and "x_studio_ref_ofc22" in self._fields:
            return (getattr(self, "x_studio_ref_ofc22", False) or "").strip()
        return (self.ref or "").strip()

    def _phc_get_effective_ref_write_vals(self, ref_value):
        self.ensure_one()
        safe_ref = (ref_value or "").strip()
        if self._phc_company_uses_ofc22_ref(self.env.company) and "x_studio_ref_ofc22" in self._fields:
            return {"x_studio_ref_ofc22": safe_ref}
        return {"ref": safe_ref}

    def _phc_is_sub_contact(self):
        """Subcontacto (pessoa/morada sob uma empresa): só a entidade comercial vai para o PHC."""
        self.ensure_one()
        return bool(self.parent_id) and self.commercial_partner_id != self

    def _get_phc_sync_block_reasons(self):
        self.ensure_one()
        reasons = []

        dup_partner = self._get_duplicate_vat_partner()
        if dup_partner:
            reasons.append(
                _("Duplicate VAT/NIF found in '%s' (ID %s).")
                % (dup_partner.display_name, dup_partner.id)
            )

        if not (self.x_studio_country_code or "").strip():
            reasons.append(_("Missing PHC field: x_studio_country_code."))

        return reasons

    def _phc_mark_sync_blocked(self, reasons):
        self.ensure_one()
        if not reasons:
            return

        message = _("PHC sync blocked: %s") % " | ".join(reasons)
        _logger.warning("PHC sync blocked for partner id=%s: %s", self.id, message)
        self.with_context(skip_phc_auto_sync=True).sudo().write(
            {
                "is_phc_synced": False,
                "phc_last_response": message,
            }
        )

    def _apply_phc_incoming_sync(self):
        if self.env.context.get("skip_phc_incoming_sync"):
            return

        for rec in self:
            vals = {}

            if rec.x_studio_salesperson_id_1:
                user = rec._get_user_by_phc_salesperson_nr(rec.x_studio_salesperson_id_1)
                if user and rec.user_id.id != user.id:
                    vals["user_id"] = user.id

            code = (rec.x_studio_country_code or "").strip().upper()
            if code:
                current_country_code = (
                    (rec.country_id.code or "").strip().upper() if rec.country_id else ""
                )
                if not rec.country_id or current_country_code != code:
                    country = self.env["res.country"].sudo().search(
                        ["|", ("code", "=", code), ("name", "=", code)],
                        limit=1,
                    )
                    if country:
                        vals["country_id"] = country.id

            if vals:
                rec.sudo().with_context(
                    skip_phc_outgoing_sync=True,
                    skip_phc_auto_sync=True,
                ).write(vals)

    def _apply_phc_outgoing_sync(self):
        if self.env.context.get("skip_phc_outgoing_sync"):
            return

        for rec in self:
            vals = {}

            new_sales_nr = rec.user_id.x_studio_salesperson_id_1 if rec.user_id else 0
            current_sales_nr = rec.x_studio_salesperson_id_1 or 0
            if (current_sales_nr or 0) != (new_sales_nr or 0):
                vals["x_studio_salesperson_id_1"] = new_sales_nr or 0

            if rec.country_id and rec.country_id.code:
                new_code = (rec.country_id.code or "").strip().upper()
                current_code = (rec.x_studio_country_code or "").strip().upper()
                if new_code and current_code != new_code:
                    vals["x_studio_country_code"] = new_code

            if vals:
                rec.sudo().with_context(
                    skip_phc_incoming_sync=True,
                    skip_phc_auto_sync=True,
                ).write(vals)

    # --------------------------------------------------------------
    # Onchange sync
    # --------------------------------------------------------------
    @api.onchange("x_studio_salesperson_id_1")
    def _onchange_phc_salesperson_id_1(self):
        for rec in self:
            if rec.x_studio_salesperson_id_1:
                user = rec._get_user_by_phc_salesperson_nr(rec.x_studio_salesperson_id_1)
                if user:
                    rec.user_id = user

    @api.onchange("user_id")
    def _onchange_user_id_to_phc_salesperson_id_1(self):
        for rec in self:
            new_val = rec.user_id.x_studio_salesperson_id_1 if rec.user_id else 0
            if (rec.x_studio_salesperson_id_1 or 0) != (new_val or 0):
                rec.x_studio_salesperson_id_1 = new_val or 0

    @api.onchange("x_studio_country_code")
    def _onchange_phc_country_code(self):
        for rec in self:
            code = (rec.x_studio_country_code or "").strip().upper()
            if not code:
                continue
            current_code = (
                (rec.country_id.code or "").strip().upper() if rec.country_id else ""
            )
            if rec.country_id and current_code == code:
                continue
            country = self.env["res.country"].sudo().search(
                ["|", ("code", "=", code), ("name", "=", code)],
                limit=1,
            )
            if country:
                rec.country_id = country

    @api.onchange("country_id")
    def _onchange_country_id_to_phc_country_code(self):
        for rec in self:
            if rec.country_id and rec.country_id.code:
                new_code = rec.country_id.code.strip().upper()
                if (rec.x_studio_country_code or "").strip().upper() != new_code:
                    rec.x_studio_country_code = new_code
            else:
                rec.x_studio_country_code = False

    # --------------------------------------------------------------
    # Constraints / Validation
    # ONLY mandatory for PHC: country code + name
    # --------------------------------------------------------------
    @api.constrains(
        "name",
        "x_studio_country_code",
        "vat",
        "street",
        "zip",
        "city",
        "email",
        "phone",
        "x_studio_salesperson_id_1",
        "x_studio_tabela_precos",
        "responsavel_interno",
        "property_payment_term_id",
        "motivo_isencao",
        "country_id",
    )
    def _check_phc_requirements(self):
        for partner in self:
            must_validate_for_phc = bool(
                partner.is_phc_synced or partner._phc_get_effective_ref() or self.env.context.get("phc_autosync")
            )
            if not must_validate_for_phc:
                continue

            missing = []
            required_fields = ["name"]
            for fname in required_fields:
                if not getattr(partner, fname):
                    missing.append(fname)

            if missing:
                raise ValidationError(
                    _("Os seguintes campos PHC são obrigatórios: %s") % ", ".join(missing)
                )

            if partner.country_id and partner.country_id.code == "PT" and partner.zip:
                if not re.match(r"^\d{4}-\d{3}$", partner.zip):
                    raise ValidationError(
                        _("O código postal português deve estar no formato 1234-123.")
                    )

            if partner.x_studio_salesperson_id_1 and partner.x_studio_salesperson_id_1 > 9999:
                raise ValidationError(_("O número do vendedor PHC deve ter no máximo 4 dígitos."))

            for fname, limit in partner.PHC_LIMITS.items():
                if fname == "property_payment_term_id":
                    value = (
                        partner.property_payment_term_id.name
                        if partner.property_payment_term_id
                        else ""
                    )
                else:
                    value = getattr(partner, fname, "") or ""
                if value and len(str(value)) > limit:
                    raise ValidationError(
                        _("O campo %s excede o limite de %s caracteres.") % (fname, limit)
                    )

    # --------------------------------------------------------------
    # Build CDATA parameter XML
    # --------------------------------------------------------------
    def _phc_build_parameter_xml(self, for_update=False):
        self.ensure_one()

        pncont = self._phc_trim(self.x_studio_country_code, self.PHC_LIMITS["x_studio_country_code"])
        nome = self._phc_trim(self.name, self.PHC_LIMITS["name"])

        ncont = self._phc_trim(self.vat, self.PHC_LIMITS["vat"])
        morada = self._phc_trim(self.street, self.PHC_LIMITS["street"])
        codpost = self._phc_trim(self.zip, self.PHC_LIMITS["zip"])
        telemovel = self._phc_trim(self.phone, self.PHC_LIMITS["phone"])
        email = self._phc_trim(self.email, self.PHC_LIMITS["email"])
        localidade = self._phc_trim(self.city, self.PHC_LIMITS["city"])

        vendedornr = ""
        if self.x_studio_salesperson_id_1:
            vendedornr = self._phc_trim(
                str(self.x_studio_salesperson_id_1),
                self.PHC_LIMITS["x_studio_salesperson_id_1"],
            )

        condpag = ""
        if self.property_payment_term_id:
            condpag = self._phc_trim(
                self.property_payment_term_id.name,
                self.PHC_LIMITS["property_payment_term_id"],
            )

        tabprecost = self._phc_trim(self.x_studio_tabela_precos, self.PHC_LIMITS["x_studio_tabela_precos"])

        codmotisencao = ""
        if self.motivo_isencao:
            codmotisencao = self._phc_trim(self.motivo_isencao, self.PHC_LIMITS["motivo_isencao"])

        no_tag = ""
        if for_update:
            if not self._phc_get_effective_ref():
                raise UserError(_("Para atualizar no PHC é obrigatório ter a referência PHC (ref)."))
            no_value = self._phc_trim(self._phc_get_effective_ref(), self.PHC_LIMITS["ref"])
            no_tag = f"<no>{no_value}</no>"

        xml_param = (
            f"{no_tag}"
            f"<pncont>{pncont}</pncont>"
            f"<ncont>{ncont}</ncont>"
            f"<nome>{nome}</nome>"
            f"<morada>{morada}</morada>"
            f"<codpost>{codpost}</codpost>"
            f"<telemovel>{telemovel}</telemovel>"
            f"<email>{email}</email>"
            f"<localidade>{localidade}</localidade>"
            f"<vendedornr>{vendedornr}</vendedornr>"
            f"<condpag>{condpag}</condpag>"
            f"<tabprecost>{tabprecost}</tabprecost>"
            f"<codmotisencao>{codmotisencao}</codmotisencao>"
        )
        return xml_param

    # --------------------------------------------------------------
    # SOAP RunCode call
    # --------------------------------------------------------------
    def _phc_run_code(self, code, parameter_xml):
        self.ensure_one()

        # Hard safety: if partner already has ref, CriaCL is forbidden and we force UpdateCL.
        normalized_code = (code or "").strip()
        if normalized_code == PHC_SCRIPT_CODE and self._phc_get_effective_ref():
            _logger.warning(
                "Blocked CriaCL for partner id=%s ref=%s; forcing UpdateCL.",
                self.id,
                self._phc_get_effective_ref(),
            )
            code = PHC_SCRIPT_UPDATE_CODE
            parameter_xml = self._phc_build_parameter_xml(for_update=True)

        company = self.env.company
        ws_url = (company.phc_api_base_url or "").strip()
        phc_user = (company.phc_api_user or "").strip()
        phc_password = (company.phc_api_password or "").strip()

        if not ws_url or not phc_user or not phc_password:
            raise UserError(
                _(
                    "Credenciais PHC em falta. "
                    "Preencha URL, utilizador e password na Configuracao para a empresa ativa."
                )
            )

        envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <RunCode xmlns="http://www.phc.pt/">
      <userName>{phc_user}</userName>
      <password>{phc_password}</password>
      <code>{code}</code>
      <parameter><![CDATA[{parameter_xml}]]></parameter>
    </RunCode>
  </soap:Body>
</soap:Envelope>
"""

        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "http://www.phc.pt/RunCode",
        }

        try:
            resp = requests.post(
                ws_url,
                data=envelope.encode("utf-8"),
                headers=headers,
                timeout=30,
                verify=False,
            )
        except Exception as e:
            _logger.exception("Erro a ligar ao PHC: %s", e)
            raise UserError(_("Erro a ligar ao PHC: %s") % e)

        if resp.status_code != 200:
            _logger.error("PHC devolveu HTTP %s: %s", resp.status_code, resp.text)
            raise UserError(_("PHC devolveu código HTTP %s") % resp.status_code)

        response_text = resp.text
        run_code_result = None
        fault_string = None

        try:
            ns = {
                "soap": "http://schemas.xmlsoap.org/soap/envelope/",
                "phc": "http://www.phc.pt/",
            }
            root = ET.fromstring(response_text)

            fault_el = root.find(".//soap:Fault", namespaces=ns)
            if fault_el is not None:
                fault_string_el = fault_el.find(".//faultstring")
                if fault_string_el is not None:
                    fault_string = fault_string_el.text

            result_el = root.find(".//phc:RunCodeResult", namespaces=ns)
            if result_el is not None:
                run_code_result = (result_el.text or "").strip()

        except Exception:
            _logger.exception("Não foi possível fazer parse ao XML de resposta do PHC.")

        if fault_string:
            raise UserError(_("PHC SOAP Fault: %s") % fault_string)

        return response_text, run_code_result

    # --------------------------------------------------------------
    # Internal helpers used by auto-sync
    # --------------------------------------------------------------
    def _phc_push_create(self, raise_on_missing_ref=False):
        """Cria o cliente no PHC.

        `raise_on_missing_ref=False` (auto-sync na gravação): NUNCA rebenta — em caso de
        erro/sem referência, regista a resposta, marca como não sincronizado e segue, para
        não bloquear fluxos como a conversão de leads ou a criação de contactos.
        `raise_on_missing_ref=True` (botões manuais): rebenta para o utilizador ver o erro.
        """
        self.ensure_one()
        # Hard rule: if ref exists, never call CriaCL; force UpdateCL instead.
        if self._phc_get_effective_ref():
            self.with_context(skip_phc_auto_sync=True).sudo().write({"is_phc_synced": True})
            self.with_context(phc_autosync=True)._phc_push_update(
                old_vat=self.vat, raise_on_missing_ref=raise_on_missing_ref)
            return

        parameter_xml = self._phc_build_parameter_xml(for_update=False)
        try:
            resp_text, run_code_result = self._phc_run_code(PHC_SCRIPT_CODE, parameter_xml)
        except Exception as e:
            if raise_on_missing_ref:
                raise
            _logger.exception("PHC create falhou (auto-sync) no parceiro %s: %s", self.id, e)
            self.with_context(skip_phc_auto_sync=True).sudo().write({
                "is_phc_synced": False,
                "phc_last_response": _("Erro PHC (auto-sync): %s") % e,
            })
            return

        vals = {"phc_last_response": resp_text}

        ref_value = self._phc_extract_ref_from_run_code_result(run_code_result)
        msg = self._phc_extract_message_from_run_code_result(run_code_result)

        if msg and not ref_value:
            vals["is_phc_synced"] = False
            self.with_context(skip_phc_auto_sync=True).sudo().write(vals)
            if raise_on_missing_ref:
                raise UserError(_("Erro ao criar cliente no PHC: %s") % msg)
            return

        if not ref_value:
            vals["is_phc_synced"] = False
            self.with_context(skip_phc_auto_sync=True).sudo().write(vals)
            if raise_on_missing_ref:
                raise UserError(_("Erro ao obter a referência do cliente após criação no PHC. Resposta: %s") % (run_code_result or resp_text))
            return

        if not self._phc_get_effective_ref():
            vals.update(self._phc_get_effective_ref_write_vals(ref_value))

        vals["is_phc_synced"] = True
        self.with_context(skip_phc_auto_sync=True).sudo().write(vals)

    def _phc_push_update(self, old_vat=None, raise_on_missing_ref=False):
        """Atualiza o cliente no PHC. Não-bloqueante no auto-sync (ver _phc_push_create)."""
        self.ensure_one()
        if not self._phc_get_effective_ref():
            if raise_on_missing_ref:
                raise UserError(_("Para atualizar no PHC é obrigatório ter a referência PHC (ref)."))
            return

        parameter_xml = self._phc_build_parameter_xml(for_update=True)
        try:
            resp_text, run_code_result = self._phc_run_code(PHC_SCRIPT_UPDATE_CODE, parameter_xml)
        except Exception as e:
            if raise_on_missing_ref:
                raise
            _logger.exception("PHC update falhou (auto-sync) no parceiro %s: %s", self.id, e)
            self.with_context(skip_phc_auto_sync=True).sudo().write({
                "phc_last_response": _("Erro PHC (auto-sync): %s") % e,
            })
            return

        self.with_context(skip_phc_auto_sync=True).sudo().write({"phc_last_response": resp_text})

        msg = self._phc_extract_message_from_run_code_result(run_code_result)
        ref_value = self._phc_extract_ref_from_run_code_result(run_code_result)

        if msg and not ref_value:
            if PHC_VAT_LOCK_MSG_SNIPPET in msg.lower():
                if old_vat is not None and (self.vat or "") != (old_vat or ""):
                    self.with_context(skip_phc_auto_sync=True).sudo().write({"vat": old_vat})
            if raise_on_missing_ref:
                raise UserError(_("Erro ao atualizar cliente no PHC: %s") % msg)

    def _phc_auto_sync_after_save(self, vals, old_vat_by_id=None):
        if self.env.context.get("skip_phc_auto_sync"):
            return

        ignored_keys = {"phc_last_response", "is_phc_synced"}
        if set(vals.keys()).issubset(ignored_keys):
            return

        if self.env.context.get("import_file"):
            for rec in self:
                has_effective_ref = bool(rec._phc_get_effective_ref())
                if rec.is_phc_synced and not has_effective_ref:
                    rec.with_context(skip_phc_auto_sync=True).sudo().write({"is_phc_synced": False})
                elif has_effective_ref and not rec.is_phc_synced:
                    rec.with_context(skip_phc_auto_sync=True).sudo().write({"is_phc_synced": True})
            return

        for rec in self:
            # Portal/public users should not trigger PHC partner autosync.
            # This avoids blocking manual portal user creation on PHC consistency checks.
            only_non_internal_users = bool(rec.user_ids) and not rec.user_ids.filtered(lambda u: u._is_internal())
            if only_non_internal_users:
                if rec.is_phc_synced and not rec._phc_get_effective_ref():
                    rec.with_context(skip_phc_auto_sync=True).sudo().write({"is_phc_synced": False})
                continue

            if rec._phc_is_sub_contact():
                continue

            block_reasons = rec._get_phc_sync_block_reasons()
            if block_reasons:
                rec._phc_mark_sync_blocked(block_reasons)
                continue

            if rec.is_phc_synced:
                if not rec._phc_get_effective_ref():
                    # Não bloquear a gravação: marcar como não sincronizado e seguir.
                    rec.with_context(skip_phc_auto_sync=True).sudo().write({"is_phc_synced": False})
                    continue
                old_vat = (old_vat_by_id or {}).get(rec.id)
                rec.with_context(phc_autosync=True)._phc_push_update(old_vat=old_vat)
            else:
                if rec._phc_get_effective_ref():
                    rec.with_context(skip_phc_auto_sync=True).sudo().write(
                        {"is_phc_synced": True}
                    )
                    old_vat = (old_vat_by_id or {}).get(rec.id)
                    rec.with_context(phc_autosync=True)._phc_push_update(old_vat=old_vat)
                    continue
                rec.with_context(phc_autosync=True)._phc_push_create()

    # --------------------------------------------------------------
    # ✅ VAT change lock BEFORE saving:
    # If partner has posted invoices/refunds, VAT cannot be changed.
    # --------------------------------------------------------------
    def write(self, vals):
        if "vat" in vals and vals.get("vat"):
            vals["vat"] = str(vals["vat"]).strip().replace(" ", "").upper()

            # PT: if PT######### -> store digits only
            for rec in self:
                if rec._is_pt_partner():
                    v = rec._normalize_vat_generic(vals.get("vat"))
                    if re.fullmatch(r"PT\d{9}", v):
                        vals["vat"] = v[2:]

        if "vat" in vals:
            for rec in self:
                old_vat = rec.vat or ""
                new_vat = vals.get("vat") or ""

                old_norm = rec._normalize_vat_generic(old_vat)
                new_norm = rec._normalize_vat_generic(new_vat)

                # for PT compare digits-only
                if rec._is_pt_partner():
                    old_norm = rec._normalize_vat_pt_digits(old_norm)
                    new_norm = rec._normalize_vat_pt_digits(new_norm)

                if old_norm != new_norm:
                    if rec._has_posted_customer_documents():
                        raise ValidationError(
                            _(
                                "Não é permitido alterar o NIF deste cliente porque já existem faturas/notas de crédito "
                                "validadas no Odoo."
                            )
                        )

        old_vat_by_id = {}
        if "vat" in vals:
            for rec in self:
                old_vat_by_id[rec.id] = rec.vat

        res = super().write(vals)

        if any(k in vals for k in ("x_studio_salesperson_id_1", "x_studio_country_code")):
            self._apply_phc_incoming_sync()
        if any(k in vals for k in ("user_id", "country_id")):
            self._apply_phc_outgoing_sync()

        self._phc_auto_sync_after_save(vals, old_vat_by_id=old_vat_by_id)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        records._apply_phc_incoming_sync()
        records._apply_phc_outgoing_sync()

        for rec, vals in zip(records, vals_list):
            rec._phc_auto_sync_after_save(vals, old_vat_by_id=None)

        return records

    # --------------------------------------------------------------
    # Manual Buttons
    # --------------------------------------------------------------
    def action_sync_phc(self):
        synced_count = 0
        blocked_count = 0
        for partner in self:
            if partner._phc_is_sub_contact():
                continue
            block_reasons = partner._get_phc_sync_block_reasons()
            if block_reasons:
                blocked_count += 1
                partner._phc_mark_sync_blocked(block_reasons)
                continue
            if partner._phc_get_effective_ref():
                old_vat = partner.vat
                partner.with_context(phc_autosync=True)._phc_push_update(
                    old_vat=old_vat, raise_on_missing_ref=True)
            else:
                partner.with_context(phc_autosync=True)._phc_push_create(raise_on_missing_ref=True)
            synced_count += 1

        if blocked_count and synced_count:
            message = _("PHC sync done for %s contact(s). Blocked %s contact(s). Check 'Ultima resposta PHC'.") % (
                synced_count,
                blocked_count,
            )
        elif blocked_count:
            message = _("PHC sync blocked for %s contact(s). Check 'Ultima resposta PHC'.") % blocked_count
        else:
            message = _("Criacao/Sync no PHC concluida. Consulte 'Ultima resposta PHC'.")
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("PHC Sync"),
                "message": _("Criação/Sync no PHC concluída. Consulte 'Última resposta PHC'."),
                "message": message,
                "sticky": False,
            },
        }

    def action_update_phc(self):
        synced_count = 0
        blocked_count = 0
        for partner in self:
            if partner._phc_is_sub_contact():
                continue
            block_reasons = partner._get_phc_sync_block_reasons()
            if block_reasons:
                blocked_count += 1
                partner._phc_mark_sync_blocked(block_reasons)
                continue
            if not partner._phc_get_effective_ref():
                raise UserError(
                    _("Este cliente ainda não tem referência PHC (ref). Use 'PHC Sync' primeiro.")
                )
            old_vat = partner.vat
            partner.with_context(phc_autosync=True)._phc_push_update(
                old_vat=old_vat, raise_on_missing_ref=True)
            synced_count += 1

        if blocked_count and synced_count:
            message = _("PHC update done for %s contact(s). Blocked %s contact(s). Check 'Ultima resposta PHC'.") % (
                synced_count,
                blocked_count,
            )
        elif blocked_count:
            message = _("PHC update blocked for %s contact(s). Check 'Ultima resposta PHC'.") % blocked_count
        else:
            message = _("Atualizacao no PHC concluida. Consulte 'Ultima resposta PHC'.")

        if blocked_count:
            raise UserError(message)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("PHC Update"),
                "message": _("Atualização no PHC concluída. Consulte 'Última resposta PHC'."),
                "sticky": False,
            },
        }
