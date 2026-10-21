# -*- coding: utf-8 -*-
import json
import logging
import re
import unicodedata
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape as xml_escape

import requests

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

# Scripts PHC
PHC_SCRIPT_CODE = "CriaCL"
PHC_SCRIPT_UPDATE_CODE = "UpdateCL"
PHC_DELIVERY_SCRIPT_CODE = "Cria_MoradaEntregaCL"

# PHC message that means "VAT change is forbidden"
PHC_VAT_LOCK_MSG_SNIPPETS = ("não pode alterar o nif", "nao pode alterar o nif")

# Marcador gravado em `phc_last_response` quando o PHC recusa o UpdateCL por causa
# do NIF sem que o save tenha alterado o NIF. Serve para não repetir a nota no
# chatter em cada gravação seguinte do mesmo contacto.
PHC_VAT_LOCK_MARKER = "[PG_PHC_VAT_LOCK]"

# ✅ VAT duplicate exceptions (placeholders allowed)
VAT_DUPLICATE_EXCEPTIONS_RAW = {"999999990", "SEM NIF"}
VAT_DUPLICATE_EXCEPTIONS = {
    re.sub(r"\s+", "", str(x)).strip().upper() for x in VAT_DUPLICATE_EXCEPTIONS_RAW
}


# Default mapping: cleaned res.users.name -> PHC respint name.
# Used by the post_init_hook and by the 2.1.0 migration so that both fresh
# installs and upgrades end up with the correct PHC user mapping.
PG_PHC_RESPONSAVEL_INTERNO_DEFAULTS = {
    "Ana Martins": "Ana Martins",
    "Bruno Bessa": "Bruno Bessa",
    "Carlos Santos": "Carlos",
    "Egídio Santos": "Egídio",
    "Elsa Silva": "Elsa",
    "Hugo Rios": "Hugo Rios",
    "Hugo Rios Export": "Hugo Rios",
    "João Neves": "Armazém",
    "Nuno Leão": "Nuno",
    "Tânia Pacheco": "Tânia",
}


def _pg_phc_clean_legacy_user_name(value):
    cleaned = (value or "").strip()
    if not cleaned:
        return ""
    if "|" in cleaned:
        cleaned = cleaned.rsplit("|", 1)[-1].strip()
    return cleaned


def apply_pg_phc_responsavel_interno_defaults(cr):
    """Apply the default cleaned-name -> PHC name mapping to res.users.

    Idempotent. Overwrites only when the current value is empty OR equals the
    cleaned user.name (i.e. the legacy value seeded by the previous migration).
    Any value the admin set manually that differs from those two is preserved.

    Pure SQL — does not touch the ORM, so no PHC sync is triggered.
    """
    cr.execute(
        """
        SELECT u.id, p.name, u.pg_phc_responsavel_interno_name
          FROM res_users u
          JOIN res_partner p ON p.id = u.partner_id
         WHERE u.share = false
        """
    )
    updated = 0
    for user_id, raw_name, current_phc_name in cr.fetchall():
        clean = _pg_phc_clean_legacy_user_name(raw_name)
        target = PG_PHC_RESPONSAVEL_INTERNO_DEFAULTS.get(clean)
        if target is None:
            continue
        current = (current_phc_name or "").strip()
        if current and current != clean and current != target:
            continue
        if current == target:
            continue
        cr.execute(
            """
            UPDATE res_users
               SET pg_phc_responsavel_interno_name = %s
             WHERE id = %s
            """,
            (target[:30], user_id),
        )
        updated += 1

    cr.execute(
        """
        UPDATE res_partner p
           SET responsavel_interno = u.pg_phc_responsavel_interno_name
          FROM res_users u
         WHERE p.pg_responsavel_interno_user_id = u.id
           AND COALESCE(p.responsavel_interno, '') IS DISTINCT FROM
               COALESCE(u.pg_phc_responsavel_interno_name, '')
        """
    )
    cr.execute(
        """
        UPDATE res_partner
           SET responsavel_interno = NULL
         WHERE pg_responsavel_interno_user_id IS NULL
           AND responsavel_interno IS NOT NULL
        """
    )
    return updated


class ResUsers(models.Model):
    _inherit = "res.users"

    x_studio_salesperson_id_1 = fields.Integer(
        string="Vendedor PHC (nº)",
        help="Número do vendedor no PHC (vendedornr). Usado para mapear parceiros (res.partner) ao user_id.",
        index=True,
    )

    pg_phc_responsavel_interno_name = fields.Char(
        string="Responsável Interno PHC (nome)",
        size=30,
        help=(
            "Nome exato deste utilizador na tabela de utilizadores PHC. "
            "Enviado para o PHC no campo respint quando este utilizador for "
            "selecionado como Responsável Interno de um contacto."
        ),
    )


class ResPartner(models.Model):
    _inherit = "res.partner"

    PHC_LIMITS = {
        "vat": 20,
        "name": 55,
        "street": 55,
        "zip": 45,
        "phone": 45,
        "pg_telefone": 45,
        "email": 100,
        "city": 43,
        "x_studio_country_code": 2,
        "x_studio_salesperson_id_1": 4,
        "property_payment_term_id": 55,
        "x_studio_tabela_precos": 1,
        "responsavel_interno": 30,
        "ref": 20,
        "motivo_isencao": 3,
        # Campos PHC da ficha de cliente Essani (cl.COBEMAIL / cl.COBTACTO)
        "pg_cobranca_email": 100,
        "pg_cobranca_contacto": 45,
    }

    PHC_DELIVERY_LIMITS = {
        "name": 60,
        "street": 55,
        "zip": 45,
        "city": 43,
        "pg_contacto_entrega": 50,
        "pg_telefone": 60,
        "email": 100,
        "phone": 45,
        "no": 10,
    }

    # User-facing labels and suggestions for PHC validation messages.
    # Keys must match the field/error identifiers used in the validators below.
    # The "zip" suggestion is intentionally absent — it's only meaningful for
    # Portuguese partners and is added dynamically in _phc_required_field_message.
    PHC_FIELD_METADATA = {
        "vat": {
            "label": "NIF",
            "suggestion": "use 'SEM NIF' ou '999999990' se desconhecido",
        },
        "name": {"label": "Nome"},
        "street": {"label": "Morada"},
        "zip": {"label": "Código Postal"},
        "city": {"label": "Localidade"},
        "email": {
            "label": "E-mail",
            "suggestion": "ex: geral@empresa.pt",
        },
        "phone": {"label": "Telemóvel"},
        "x_studio_country_code": {
            "label": "Código País",
            "suggestion": "ex: PT, ES, FR",
        },
        "x_studio_salesperson_id_1": {
            "label": "Vendedor PHC (nº)",
            "suggestion": "selecione o Vendedor no campo 'Vendedor' — o nº é preenchido automaticamente",
        },
        "responsavel_interno": {
            "label": "Responsável Interno",
            "suggestion": (
                "selecione o utilizador interno responsável pelo cliente "
                "(o nome PHC do utilizador deve estar configurado em "
                "Definições → Utilizadores)"
            ),
        },
        "property_payment_term_id": {
            "label": "Condições de Pagamento",
            "suggestion": "ex: Pronto Pagamento, 30 dias",
        },
        "motivo_isencao": {
            "label": "Motivo de Isenção",
            "suggestion": "selecione o motivo (ex: M07 — Isento artigo 9.º do CIVA)",
        },
        "pg_cobranca_email": {
            "label": "Email para cobranças",
            "suggestion": "ex: cobranca@empresa.pt",
        },
        "pg_cobranca_contacto": {
            "label": "Nome para contactos de cobrança",
        },
    }

    PHC_DELIVERY_FIELD_METADATA = {
        "name": {
            "label": "Nome da morada de entrega",
            "suggestion": "ex: Armazém Lisboa",
        },
        "street": {"label": "Morada"},
        "zip": {
            "label": "Código Postal",
            "suggestion": "formato 1234-123 quando o país é Portugal",
        },
        "city": {"label": "Localidade"},
        "parent_id": {
            "label": "Cliente principal",
            "suggestion": "associe esta morada de entrega a um cliente",
        },
        "no": {
            "label": "Nº do cliente PHC",
            "suggestion": "o cliente principal tem de estar sincronizado com o PHC primeiro",
        },
        "pais": {
            "label": "País",
            "suggestion": "preencha o país do cliente (ex: Portugal)",
        },
    }

    # -----------------------------
    # PHC toggle
    # -----------------------------
    is_phc_synced = fields.Boolean(
        string="PHC Synced",
        default=False,
        help=(
            "Indica que o contacto já está ligado ao PHC. Novos contactos não são "
            "enviados automaticamente; use o botão de sync quando a ficha estiver completa. "
            "Depois de existir ref PHC, as alterações passam a ser atualizadas no save."
        ),
    )

    phc_last_response = fields.Text(
        string="Última resposta PHC",
        readonly=True,
        help="Resposta bruta do serviço PHC (para debug).",
    )

    pg_obs = fields.Text(
        string="Notas PHC (obs)",
        help="Notas adicionais enviadas ao PHC no campo obs.",
    )

    # -----------------------------
    # Fields
    # -----------------------------
    x_studio_country_code = fields.Char(
        string="Código País PHC",
        size=PHC_LIMITS["x_studio_country_code"],
        help="Código de país PHC (pncont). Ex: PT",
    )

    x_studio_salesperson_id_1 = fields.Integer(
        string="Vendedor PHC (nº)",
        help="Número do vendedor no PHC (vendedornr). Vai procurar o utilizador cujo res.users.x_studio_salesperson_id_1 seja igual.",
        index=True,
    )

    x_studio_salesperson_id = fields.Integer(
        string="Vendedor PHC old",
        help="Número do vendedor no PHC (vendedornr) old",
    )

    x_studio_tabela_precos = fields.Selection(
        selection=[("1", "Tab"), ("2", "P01"), ("3", "P02"), ("4", "RV1"), ("5", "RV2")],
        default="1",
        string="Tabela de Preços (PHC)",
        help="Tabela de preços PHC (tabprecost).",
    )

    pg_portes_gratuitos = fields.Boolean(
        string="Portes Gratuitos (PHC)",
        help="Enviado ao PHC como portesgratuitos (0/1).",
    )

    pg_telefone = fields.Char(
        string="Telefone (PHC)",
        size=PHC_DELIVERY_LIMITS["pg_telefone"],
        help="Enviado ao PHC como telefone.",
    )

    pg_contacto_entrega = fields.Char(
        string="Contacto Entrega (PHC)",
        size=PHC_DELIVERY_LIMITS["pg_contacto_entrega"],
        help="Nome do contacto enviado ao PHC para moradas de entrega.",
    )

    pg_responsavel_interno_user_id = fields.Many2one(
        "res.users",
        string="Responsavel Interno (Odoo)",
        domain="[('share', '=', False), ('pg_phc_responsavel_interno_name', '!=', False)]",
        help=(
            "Selecione um utilizador Odoo interno. O nome PHC associado ao "
            "utilizador é o que vai para o PHC. Configure o nome PHC em "
            "Definições → Utilizadores."
        ),
    )

    responsavel_interno = fields.Char(
        string="Responsável Interno (PHC)",
        size=PHC_LIMITS["responsavel_interno"],
        related="pg_responsavel_interno_user_id.pg_phc_responsavel_interno_name",
        store=True,
        readonly=True,
        help="Responsável interno (respint) — definido em Definições → Utilizadores.",
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

    # -----------------------------------------------------------------
    # Campos PHC da ficha de cliente Essani (sincronizados com o PHC)
    #   pg_insolvente         -> cl.U_INSOLV  (lógico)  -> param insolvente
    #   pg_nao_email_cc       -> cl.NAOMAIL   (lógico)  -> param naoemailcc
    #   pg_cobranca_email     -> cl.COBEMAIL  (char 100)-> param cobemail
    #   pg_cobranca_contacto  -> cl.COBTACTO  (char 45) -> param cobcontacto
    # Os lógicos são enviados como "true"/"false" (formato aceite pelo PHC,
    # conforme exemplo dos parâmetros do serviço de sincronismo).
    # -----------------------------------------------------------------
    pg_insolvente = fields.Boolean(
        string="Insolvente (PHC)",
        help="Indica que o cliente está insolvente. Enviado ao PHC como insolvente (cl.U_INSOLV).",
    )

    pg_nao_email_cc = fields.Boolean(
        string="Não recebe mailing de c/c (PHC)",
        help="Cliente não recebe mailing de conta-corrente. Enviado ao PHC como naoemailcc (cl.NAOMAIL).",
    )

    pg_cobranca_email = fields.Char(
        string="Email para cobranças (PHC)",
        size=PHC_LIMITS["pg_cobranca_email"],
        help="Email dedicado a cobranças. Enviado ao PHC como cobemail (cl.COBEMAIL).",
    )

    pg_cobranca_contacto = fields.Char(
        string="Nome para contactos de cobrança (PHC)",
        size=PHC_LIMITS["pg_cobranca_contacto"],
        help="Nome do contacto para cobranças. Enviado ao PHC como cobcontacto (cl.COBTACTO).",
    )

    # --------------------------------------------------------------
    # Utils
    # --------------------------------------------------------------
    @staticmethod
    def _phc_trim(value, limit):
        if not value:
            return ""
        return str(value)[:limit]

    def _phc_required_field_message(self, fname, metadata):
        """Build a friendly PT-PT message for a missing required PHC field.

        The base label/suggestion comes from ``metadata`` but a few fields get
        contextual refinements (e.g. zip and vat depend on whether the partner
        is Portuguese; country code suggests the partner's current country).
        """
        meta = metadata.get(fname, {})
        label = meta.get("label") or fname
        suggestion = meta.get("suggestion")

        if fname == "zip" and self._is_pt_partner():
            suggestion = _("formato 1234-123, ex: 2750-642")
        elif fname == "vat" and self._is_pt_partner():
            suggestion = _(
                "9 dígitos sem o prefixo PT, ou 'SEM NIF' / '999999990' se desconhecido"
            )
        elif fname == "x_studio_country_code":
            country_code = (self.country_id.code or "").strip().upper() if self.country_id else ""
            suggestion = _("ex: %s") % (country_code or "PT")

        if suggestion:
            return _("Campo %(label)s é obrigatório (%(suggestion)s).") % {
                "label": label,
                "suggestion": suggestion,
            }
        return _("Campo %s é obrigatório.") % label

    @staticmethod
    def _phc_format_validation_message(errors, intro=None):
        intro = intro or _(
            "Não foi possível sincronizar o contacto com o PHC. "
            "Corrija os seguintes campos:"
        )
        bullets = "\n".join("  • %s" % err for err in errors)
        return "%s\n\n%s" % (intro, bullets)

    @staticmethod
    def _normalize_vat(vat):
        """Normalize VAT for comparison (trim, remove whitespace, uppercase)."""
        if not vat:
            return ""
        return re.sub(r"\s+", "", str(vat)).strip().upper()

    def _normalize_vat_pt_digits(self, vat):
        vat_norm = self._normalize_vat(vat)
        if vat_norm.startswith("PT") and re.fullmatch(r"PT\d{9}", vat_norm):
            return vat_norm[2:]
        return vat_norm

    def _pg_is_own_company_partner(self):
        """True when the partner is one of our own companies (or an address of it).

        Saving Settings -> Companies writes through to the res.company partner.
        Without this guard every such save pushed our own company to PHC as a
        customer and died on the customer-only required fields (Responsavel
        Interno, Vendedor, Condicoes de Pagamento), which made the company's
        own VAT, phone and email impossible to correct.
        """
        self.ensure_one()
        commercial = self.commercial_partner_id or self
        partner_ids = [pid for pid in {self.id, commercial.id} if pid]
        if not partner_ids:
            return False
        return bool(
            self.env["res.company"].sudo().search_count([("partner_id", "in", partner_ids)])
        )

    def _pg_is_phc_company_contact(self):
        self.ensure_one()
        return bool(self.is_company) and not self._pg_is_own_company_partner()

    def _pg_is_phc_delivery_contact(self):
        self.ensure_one()
        return self.type == "delivery" and not self._pg_is_own_company_partner()

    def _pg_is_phc_supported_contact(self):
        self.ensure_one()
        return self._pg_is_phc_company_contact() or self._pg_is_phc_delivery_contact()

    def _pg_get_delivery_parent_for_phc(self):
        self.ensure_one()
        parent = self.commercial_partner_id if self.commercial_partner_id and self.commercial_partner_id != self else self.parent_id
        return parent if parent and parent.exists() else self.env["res.partner"]

    def _pg_get_delivery_parent_ref_for_phc(self):
        self.ensure_one()
        parent = self._pg_get_delivery_parent_for_phc()
        return parent._phc_get_effective_ref().strip() if parent else ""

    def _pg_get_delivery_contacto_for_phc(self):
        self.ensure_one()
        return (self.pg_contacto_entrega or "").strip()

    def _pg_get_delivery_street_for_phc(self):
        self.ensure_one()
        parts = [part.strip() for part in (self.street, self.street2) if part and part.strip()]
        return ", ".join(parts)

    def _pg_get_phc_country_code(self):
        self.ensure_one()
        phc_code = (self.x_studio_country_code or "").strip().upper()
        if phc_code:
            return phc_code
        return (self.country_id.code or "").strip().upper() if self.country_id else ""

    def _is_pt_partner(self):
        """
        PT detection for PHC rules:
        - prefer x_studio_country_code when filled
        - otherwise fallback to country_id.code
        """
        self.ensure_one()
        return self._pg_get_phc_country_code() == "PT"

    def _get_user_by_phc_salesperson_nr(self, salesperson_nr):
        if not salesperson_nr:
            return self.env["res.users"]
        return self.env["res.users"].sudo().search(
            [("x_studio_salesperson_id_1", "=", int(salesperson_nr))],
            limit=1,
        )

    def _pg_get_responsavel_interno_for_phc(self):
        self.ensure_one()
        return (self.responsavel_interno or "").strip()

    def _pg_get_tabela_precos_for_phc(self):
        self.ensure_one()
        return str(self.x_studio_tabela_precos or "1").strip() or "1"

    def _pg_get_portes_gratuitos_for_phc(self):
        self.ensure_one()
        return "1" if self.pg_portes_gratuitos else "0"

    def _pg_get_obsint_for_phc(self):
        self.ensure_one()
        return (tools.html2plaintext(self.comment or "") or "").strip()

    def _pg_get_obs_for_phc(self):
        self.ensure_one()
        return (self.pg_obs or "").strip()

    def _pg_get_insolvente_for_phc(self):
        # Lógico PHC: enviado como "true"/"false" (ver exemplo do serviço de sync).
        self.ensure_one()
        return "true" if self.pg_insolvente else "false"

    def _pg_get_nao_email_cc_for_phc(self):
        self.ensure_one()
        return "true" if self.pg_nao_email_cc else "false"

    def _pg_get_cobemail_for_phc(self):
        self.ensure_one()
        return (self.pg_cobranca_email or "").strip()

    def _pg_get_cobcontacto_for_phc(self):
        self.ensure_one()
        return (self.pg_cobranca_contacto or "").strip()

    @staticmethod
    def _pg_escape_phc_xml(value, limit=None, keep_apostrophe=False):
        text = "" if value is None else str(value)
        if limit:
            text = text[:limit]
        if not keep_apostrophe:
            # O CriaCL/UpdateCL do PHC concatena o valor num comando SQL: uma
            # pelica fecha a string e rebenta o script. Enviamos o acento agudo
            # (U+00B4), que existe em Latin-1/Windows-1252 e valida no SAF-T.
            text = text.replace("'", "´")
        return xml_escape(text)

    def _pg_is_native_import(self):
        return bool(self.env.context.get("import_file"))

    @staticmethod
    def _pg_log_excerpt(value, limit=800):
        text = "" if value is None else str(value)
        return text if len(text) <= limit else text[:limit] + "...<truncated>"

    def _pg_get_phc_debug_snapshot(self):
        self.ensure_one()
        return {
            "id": self.id,
            "display_name": self.display_name,
            "type": self.type or "",
            "is_company": bool(self.is_company),
            "parent_id": self.parent_id.id if self.parent_id else 0,
            "delivery_parent_ref": self._pg_get_delivery_parent_ref_for_phc() if self._pg_is_phc_delivery_contact() else "",
            "country_id_code": (self.country_id.code or "").strip().upper() if self.country_id else "",
            "x_studio_country_code": (self.x_studio_country_code or "").strip().upper(),
            "zip": self.zip or "",
            "vat": self.vat or "",
            "pg_telefone": self.pg_telefone or "",
            "pg_contacto_entrega": self.pg_contacto_entrega or "",
            "x_studio_salesperson_id_1": self.x_studio_salesperson_id_1 or 0,
            "x_studio_tabela_precos_raw": self.x_studio_tabela_precos or "",
            "x_studio_tabela_precos_effective": self._pg_get_tabela_precos_for_phc(),
            "pg_portes_gratuitos": self.pg_portes_gratuitos,
            "portesgratuitos_effective": self._pg_get_portes_gratuitos_for_phc(),
            "pg_insolvente": self.pg_insolvente,
            "pg_nao_email_cc": self.pg_nao_email_cc,
            "cobemail": self._pg_get_cobemail_for_phc(),
            "cobcontacto": self._pg_get_cobcontacto_for_phc(),
            "responsavel_interno": self.responsavel_interno or "",
            "responsavel_interno_effective": self._pg_get_responsavel_interno_for_phc(),
            "obs_excerpt": self._pg_log_excerpt(self._pg_get_obs_for_phc(), limit=120),
            "obsint_excerpt": self._pg_log_excerpt(self._pg_get_obsint_for_phc(), limit=120),
            "property_payment_term_id": self.property_payment_term_id.name if self.property_payment_term_id else "",
            "effective_ref": self._phc_get_effective_ref(),
            "is_pt_partner": self._is_pt_partner(),
        }

    def _has_posted_customer_documents(self):
        """Block VAT change if partner has posted customer invoices/refunds."""
        self.ensure_one()
        Move = self.env["account.move"].sudo()
        return bool(
            Move.search_count(
                [
                    ("partner_id", "=", self.id),
                    ("state", "=", "posted"),
                    ("move_type", "in", ("out_invoice", "out_refund")),
                ]
            )
        )

    @staticmethod
    def _phc_find_value_in_payload(payload, candidate_keys):
        normalized_keys = {str(key).lower() for key in candidate_keys}

        if isinstance(payload, dict):
            for key, value in payload.items():
                if str(key).lower() in normalized_keys and value not in (None, "", False):
                    return str(value).strip()
            for value in payload.values():
                nested = ResPartner._phc_find_value_in_payload(value, candidate_keys)
                if nested:
                    return nested

        if isinstance(payload, list):
            for item in payload:
                nested = ResPartner._phc_find_value_in_payload(item, candidate_keys)
                if nested:
                    return nested

        return ""

    @staticmethod
    def _phc_extract_ref_from_run_code_result(run_code_result):
        if not run_code_result:
            return ""

        text = (run_code_result or "").strip()

        try:
            data = json.loads(text)
            ref_value = ResPartner._phc_find_value_in_payload(
                data,
                ("Numero", "numero", "No", "no", "Ref", "ref"),
            )
            if ref_value:
                return ref_value
        except Exception:
            pass

        m = re.search(
            r'"(?:Numero|numero|No|no|Ref|ref)"\s*:\s*"?(?P<num>[^",}\]]+)"?',
            text,
        )
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
            message = ResPartner._phc_find_value_in_payload(
                data,
                ("Mensagem", "mensagem", "Message", "message"),
            )
            if message:
                return message
        except Exception:
            pass

        match = re.search(r'"(?:Mensagem|mensagem|Message|message)"\s*:\s*"(?P<msg>[^"]+)"', text)
        return match.group("msg").strip() if match else ""

    def _phc_should_update(self):
        self.ensure_one()
        return bool(self._phc_get_effective_ref())

    @staticmethod
    def _phc_company_uses_ofc22_ref(company):
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

    def _get_duplicate_vat_partner(self):
        self.ensure_one()
        if not self.vat:
            return self.env["res.partner"]

        raw = self._normalize_vat(self.vat)
        if not raw or raw in VAT_DUPLICATE_EXCEPTIONS:
            return self.env["res.partner"]

        vat_norm = self._normalize_vat_pt_digits(raw) if self._is_pt_partner() else raw
        if not vat_norm:
            return self.env["res.partner"]

        others = self.env["res.partner"].sudo().search([("id", "!=", self.id), ("vat", "!=", False)])
        for other in others:
            other_raw = self._normalize_vat(other.vat)
            if not other_raw or other_raw in VAT_DUPLICATE_EXCEPTIONS:
                continue

            other_norm = (
                other._normalize_vat_pt_digits(other_raw) if other._is_pt_partner() else other_raw
            )
            if other_norm == vat_norm:
                return other

        return self.env["res.partner"]

    def _get_phc_sync_block_reasons(self):
        self.ensure_one()
        reasons = []

        if self._pg_is_own_company_partner():
            reasons.append(_(
                "Este contacto é a nossa própria empresa, não um cliente: "
                "não é sincronizado com o PHC."
            ))
            return reasons

        if not self._pg_is_phc_supported_contact():
            reasons.append(_(
                "A sincronização com o PHC só está disponível para contactos do tipo "
                "Empresa ou para moradas de entrega."
            ))
            return reasons

        if self._pg_is_phc_company_contact():
            dup_partner = self._get_duplicate_vat_partner()
            if dup_partner:
                reasons.append(
                    _("NIF duplicado: já existe no contacto '%(partner)s' (ID %(id)s).")
                    % {"partner": dup_partner.display_name, "id": dup_partner.id}
                )

        try:
            self._phc_validate_sync_requirements()
        except ValidationError as exc:
            reasons.append(exc.args[0] if exc.args else _("Validação PHC falhou."))

        return reasons

    def _phc_mark_sync_blocked(self, reasons):
        """Raise a popup describing why PHC sync is blocked.

        Previously this stored the message silently in ``phc_last_response`` so
        the save would succeed. The popup is more visible: the user sees the
        full bullet list of issues immediately. The save's transaction rolls
        back, but the form keeps the user's edits client-side so they can fix
        the missing fields and save again without retyping.
        """
        self.ensure_one()
        if not reasons:
            return

        message = _("Sincronização com o PHC bloqueada:\n\n%s") % "\n\n".join(reasons)
        _logger.warning("PHC sync blocked for partner id=%s: %s", self.id, message)
        raise UserError(message)

    def _phc_validate_sync_requirements(self):
        company_partners = self.filtered(lambda partner: partner._pg_is_phc_company_contact())
        delivery_partners = self.filtered(lambda partner: partner._pg_is_phc_delivery_contact())
        unsupported_partners = self - company_partners - delivery_partners

        if unsupported_partners:
            raise ValidationError(_(
                "A sincronização com o PHC só está disponível para contactos do tipo "
                "Empresa ou para moradas de entrega."
            ))

        if delivery_partners:
            self._phc_validate_delivery_sync_requirements(delivery_partners)

        for partner in company_partners:
            errors = []
            missing_field_names = []

            required_fields = [
                "vat",
                "name",
                "street",
                "zip",
                "city",
                "email",
                "phone",
                "x_studio_country_code",
                "x_studio_salesperson_id_1",
                "responsavel_interno",
            ]
            for fname in required_fields:
                if not getattr(partner, fname):
                    missing_field_names.append(fname)
                    errors.append(partner._phc_required_field_message(fname, partner.PHC_FIELD_METADATA))

            if not partner.property_payment_term_id:
                missing_field_names.append("property_payment_term_id")
                errors.append(partner._phc_required_field_message(
                    "property_payment_term_id", partner.PHC_FIELD_METADATA,
                ))

            if partner._is_pt_partner() and partner.zip and not re.match(r"^\d{4}-\d{3}$", partner.zip):
                errors.append(_(
                    "Código Postal: formato inválido para Portugal. "
                    "Use o formato 1234-123 (ex: 2750-642)."
                ))
                _logger.warning(
                    "PHC validation rejected PT zip for partner %s | snapshot=%s",
                    partner.id,
                    partner._pg_get_phc_debug_snapshot(),
                )

            if partner.x_studio_salesperson_id_1 and partner.x_studio_salesperson_id_1 > 9999:
                errors.append(_(
                    "Vendedor PHC (nº): deve ter no máximo 4 dígitos (entre 1 e 9999)."
                ))

            for fname, limit in partner.PHC_LIMITS.items():
                if fname in {"x_studio_salesperson_id_1", "x_studio_salesperson_id"}:
                    continue
                if fname == "property_payment_term_id":
                    value = partner.property_payment_term_id.name or ""
                else:
                    value = getattr(partner, fname, "") or ""
                current_len = len(str(value))
                if current_len > limit:
                    friendly = partner.PHC_FIELD_METADATA.get(fname, {}).get("label", fname)
                    errors.append(_(
                        "%(field)s: excede o limite de %(limit)s caracteres "
                        "(atualmente tem %(current)s)."
                    ) % {"field": friendly, "limit": limit, "current": current_len})
                    _logger.warning(
                        "PHC validation length overflow for partner %s | field=%s | limit=%s | value=%s | snapshot=%s",
                        partner.id,
                        fname,
                        limit,
                        partner._pg_log_excerpt(value, limit=250),
                        partner._pg_get_phc_debug_snapshot(),
                    )

            if missing_field_names:
                _logger.warning(
                    "PHC validation missing required fields for partner %s: %s | snapshot=%s",
                    partner.id,
                    missing_field_names,
                    partner._pg_get_phc_debug_snapshot(),
                )

            if errors:
                raise ValidationError(self._phc_format_validation_message(errors))

    def _phc_validate_delivery_sync_requirements(self, partners):
        delivery_intro = _(
            "Não foi possível sincronizar a morada de entrega com o PHC. "
            "Corrija os seguintes campos:"
        )

        for partner in partners:
            errors = []
            missing_field_names = []

            for fname in ("name", "street", "zip", "city"):
                if not getattr(partner, fname):
                    missing_field_names.append(fname)
                    errors.append(partner._phc_required_field_message(
                        fname, partner.PHC_DELIVERY_FIELD_METADATA,
                    ))

            if not partner._pg_get_delivery_parent_for_phc():
                missing_field_names.append("parent_id")
                errors.append(partner._phc_required_field_message(
                    "parent_id", partner.PHC_DELIVERY_FIELD_METADATA,
                ))

            parent_ref = partner._pg_get_delivery_parent_ref_for_phc()
            if not parent_ref:
                missing_field_names.append("no")
                errors.append(partner._phc_required_field_message(
                    "no", partner.PHC_DELIVERY_FIELD_METADATA,
                ))

            if not partner._pg_get_phc_country_code():
                missing_field_names.append("pais")
                errors.append(partner._phc_required_field_message(
                    "pais", partner.PHC_DELIVERY_FIELD_METADATA,
                ))

            if partner._is_pt_partner() and partner.zip and not re.match(r"^\d{4}-\d{3}$", partner.zip):
                errors.append(_(
                    "Código Postal: formato inválido para Portugal. "
                    "Use o formato 1234-123 (ex: 2750-642)."
                ))

            if parent_ref and not re.fullmatch(r"\d{1,10}", str(parent_ref).strip()):
                errors.append(_(
                    "Nº do cliente PHC do cliente principal: tem de ser numérico "
                    "e ter no máximo 10 dígitos."
                ))

            delivery_values = {
                "name": partner.name or "",
                "street": partner._pg_get_delivery_street_for_phc(),
                "zip": partner.zip or "",
                "city": partner.city or "",
                "pg_contacto_entrega": partner._pg_get_delivery_contacto_for_phc(),
                "pg_telefone": partner.pg_telefone or "",
                "email": partner.email or "",
                "phone": partner.phone or "",
                "no": parent_ref or "",
            }
            for fname, limit in partner.PHC_DELIVERY_LIMITS.items():
                value = delivery_values.get(fname, "") or ""
                current_len = len(str(value))
                if current_len > limit:
                    friendly = partner.PHC_DELIVERY_FIELD_METADATA.get(fname, {}).get("label", fname)
                    errors.append(_(
                        "%(field)s: excede o limite de %(limit)s caracteres "
                        "(atualmente tem %(current)s) na morada de entrega."
                    ) % {"field": friendly, "limit": limit, "current": current_len})

            if missing_field_names:
                _logger.warning(
                    "PHC delivery validation missing required fields for partner %s: %s | snapshot=%s",
                    partner.id,
                    missing_field_names,
                    partner._pg_get_phc_debug_snapshot(),
                )

            if errors:
                raise ValidationError(self._phc_format_validation_message(errors, intro=delivery_intro))

    # --------------------------------------------------------------
    # ✅ NEW: PT VAT format rule (9 digits only) except "SEM NIF"
    # Trigger on create + write (constraint).
    # --------------------------------------------------------------
    @api.constrains("vat", "country_id", "x_studio_country_code")
    def _check_pt_vat_format(self):
        if self._pg_is_native_import():
            return
        for rec in self:
            if not rec._pg_is_phc_company_contact():
                continue
            if not rec.vat:
                continue

            vat_norm = rec._normalize_vat(rec.vat)
            if not vat_norm:
                continue

            # Always allow placeholders
            if vat_norm in VAT_DUPLICATE_EXCEPTIONS:
                continue

            # If Portugal partner: VAT must be exactly 9 digits (no PT prefix, no spaces)
            if rec._is_pt_partner():
                if not re.fullmatch(r"\d{9}", vat_norm):
                    raise ValidationError(
                        _(
                            "Para clientes com país Portugal (PT), o NIF deve ter exatamente 9 dígitos "
                            "(ex: 123456789). Alternativamente pode usar o placeholder 'SEM NIF'."
                        )
                    )

    # --------------------------------------------------------------
    # ✅ VAT must be unique across partners (with exceptions)
    # --------------------------------------------------------------
    @api.constrains("vat")
    def _check_unique_vat(self):
        # Duplicate VAT should not block Odoo contact creation/update.
        # It is handled as a PHC sync blocker instead.
        return

    # --------------------------------------------------------------
    #  AUTOMATIONS EMBEDDED (Auto 1,2,3,4)
    # --------------------------------------------------------------
    def _apply_phc_incoming_sync(self):
        if self.env.context.get("skip_phc_incoming_sync"):
            return

        for rec in self:
            if not rec._pg_is_phc_company_contact():
                continue
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
            if not rec._pg_is_phc_company_contact():
                continue
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
    # Immediate UI sync (not only on save)
    # --------------------------------------------------------------
    @api.onchange("x_studio_salesperson_id_1")
    def _onchange_phc_salesperson_id_1(self):
        for rec in self:
            if not rec._pg_is_phc_company_contact():
                continue
            if rec.x_studio_salesperson_id_1:
                user = rec._get_user_by_phc_salesperson_nr(rec.x_studio_salesperson_id_1)
                if user:
                    rec.user_id = user

    @api.onchange("user_id")
    def _onchange_user_id_to_phc_salesperson_id_1(self):
        for rec in self:
            if not rec._pg_is_phc_company_contact():
                continue
            new_val = rec.user_id.x_studio_salesperson_id_1 if rec.user_id else 0
            if (rec.x_studio_salesperson_id_1 or 0) != (new_val or 0):
                rec.x_studio_salesperson_id_1 = new_val or 0

    @api.onchange("x_studio_country_code")
    def _onchange_phc_country_code(self):
        for rec in self:
            if not rec._pg_is_phc_company_contact():
                continue
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
            if not rec._pg_is_phc_company_contact():
                continue
            if rec.country_id and rec.country_id.code:
                new_code = rec.country_id.code.strip().upper()
                if (rec.x_studio_country_code or "").strip().upper() != new_code:
                    rec.x_studio_country_code = new_code
            else:
                rec.x_studio_country_code = False

    # --------------------------------------------------------------
    # Constraints / Validation
    # --------------------------------------------------------------
    @api.constrains(
        "vat",
        "name",
        "street",
        "zip",
        "city",
        "email",
        "phone",
        "pg_telefone",
        "pg_contacto_entrega",
        "x_studio_country_code",
        "x_studio_salesperson_id_1",
        "x_studio_tabela_precos",
        "pg_responsavel_interno_user_id",
        "country_id",
        "property_payment_term_id",
        "motivo_isencao",
        "pg_insolvente",
        "pg_nao_email_cc",
        "pg_cobranca_email",
        "pg_cobranca_contacto",
        "is_phc_synced",
        "is_company",
        "type",
        "parent_id",
        "ref",
    )
    def _check_phc_requirements(self):
        if self._pg_is_native_import():
            return
        for partner in self:
            must_validate_for_phc = bool(
                (
                    partner._pg_is_phc_company_contact()
                    and (
                        partner.is_phc_synced
                        or partner._phc_get_effective_ref()
                        or self.env.context.get("phc_autosync")
                    )
                )
                or (
                    partner._pg_is_phc_delivery_contact()
                    and self.env.context.get("phc_autosync")
                )
            )
            if not must_validate_for_phc:
                continue
            partner._phc_validate_sync_requirements()

    # --------------------------------------------------------------
    # Build CDATA parameter XML
    # --------------------------------------------------------------
    def _phc_build_parameter_xml(self, for_update=False, include_vat=False):
        """Constroi o XML de parametros para os scripts PHC.

        `include_vat` só é considerado nas atualizações (`for_update=True`): o PHC
        recusa qualquer UpdateCL que traga o NIF de um cliente com documentos
        certificados emitidos, mesmo quando o NIF enviado é igual ao que já tem.
        Como o auto-sync dispara em todas as gravações do contacto, enviar sempre
        `ncont`/`pncont` fazia com que uma alteração de, por exemplo, termos de
        pagamento fosse recusada pelo PHC e perdida no Odoo.

        Regra em vigor: o CriaCL leva sempre o NIF; o UpdateCL só o leva quando a
        gravação alterou mesmo o NIF no Odoo.
        """
        self.ensure_one()

        pncont = self._phc_trim(self.x_studio_country_code, self.PHC_LIMITS["x_studio_country_code"])
        ncont = self._phc_trim(self.vat, self.PHC_LIMITS["vat"])
        nome = self._phc_trim(self.name, self.PHC_LIMITS["name"])
        morada = self._phc_trim(self.street, self.PHC_LIMITS["street"])
        codpost = self._phc_trim(self.zip, self.PHC_LIMITS["zip"])
        telemovel = self._phc_trim(self.phone, self.PHC_LIMITS["phone"])
        telefone = self._phc_trim(self.pg_telefone, self.PHC_LIMITS["pg_telefone"])
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

        respint = self._phc_trim(
            self._pg_get_responsavel_interno_for_phc(),
            self.PHC_LIMITS["responsavel_interno"],
        )
        tabprecost = self._phc_trim(
            self._pg_get_tabela_precos_for_phc(),
            self.PHC_LIMITS["x_studio_tabela_precos"],
        )
        portesgratuitos = self._pg_get_portes_gratuitos_for_phc()
        insolvente = self._pg_get_insolvente_for_phc()
        naoemailcc = self._pg_get_nao_email_cc_for_phc()
        cobemail = self._phc_trim(self._pg_get_cobemail_for_phc(), self.PHC_LIMITS["pg_cobranca_email"])
        cobcontacto = self._phc_trim(
            self._pg_get_cobcontacto_for_phc(), self.PHC_LIMITS["pg_cobranca_contacto"]
        )
        obs = self._pg_get_obs_for_phc()
        obsint = self._pg_get_obsint_for_phc()

        codmotisencao = ""
        if self.motivo_isencao:
            codmotisencao = self._phc_trim(self.motivo_isencao, self.PHC_LIMITS["motivo_isencao"])

        no_tag = ""
        effective_ref = self._phc_get_effective_ref()
        if for_update and effective_ref:
            no_value = self._phc_trim(effective_ref, self.PHC_LIMITS["ref"])
            no_tag = f"<no>{self._pg_escape_phc_xml(no_value)}</no>"

        send_vat = include_vat or not for_update
        vat_tags = ""
        if send_vat:
            vat_tags = (
                f"<pncont>{self._pg_escape_phc_xml(pncont)}</pncont>"
                f"<ncont>{self._pg_escape_phc_xml(ncont)}</ncont>"
            )

        xml_param = (
            f"{no_tag}"
            f"{vat_tags}"
            f"<nome>{self._pg_escape_phc_xml(nome)}</nome>"
            f"<morada>{self._pg_escape_phc_xml(morada)}</morada>"
            f"<codpost>{self._pg_escape_phc_xml(codpost)}</codpost>"
            f"<telemovel>{self._pg_escape_phc_xml(telemovel)}</telemovel>"
            f"<telefone>{self._pg_escape_phc_xml(telefone)}</telefone>"
            f"<email>{self._pg_escape_phc_xml(email, keep_apostrophe=True)}</email>"
            f"<localidade>{self._pg_escape_phc_xml(localidade)}</localidade>"
            f"<vendedornr>{self._pg_escape_phc_xml(vendedornr)}</vendedornr>"
            f"<condpag>{self._pg_escape_phc_xml(condpag)}</condpag>"
            f"<respint>{self._pg_escape_phc_xml(respint)}</respint>"
            f"<tabprecost>{self._pg_escape_phc_xml(tabprecost)}</tabprecost>"
            f"<portesgratuitos>{self._pg_escape_phc_xml(portesgratuitos)}</portesgratuitos>"
            f"<insolvente>{self._pg_escape_phc_xml(insolvente)}</insolvente>"
            f"<naoemailcc>{self._pg_escape_phc_xml(naoemailcc)}</naoemailcc>"
            f"<cobemail>{self._pg_escape_phc_xml(cobemail, keep_apostrophe=True)}</cobemail>"
            f"<cobcontacto>{self._pg_escape_phc_xml(cobcontacto)}</cobcontacto>"
            f"<obs>{self._pg_escape_phc_xml(obs)}</obs>"
            f"<obsint>{self._pg_escape_phc_xml(obsint)}</obsint>"
            f"<codmotisencao>{self._pg_escape_phc_xml(codmotisencao)}</codmotisencao>"
        )
        _logger.info(
            "PHC parameter XML built for partner %s | for_update=%s | send_vat=%s | snapshot=%s | parameter_xml=%s",
            self.id,
            for_update,
            send_vat,
            self._pg_get_phc_debug_snapshot(),
            self._pg_log_excerpt(xml_param),
        )
        return xml_param

    def _phc_build_delivery_parameter_xml(self):
        self.ensure_one()

        parent_ref = self._phc_trim(
            self._pg_get_delivery_parent_ref_for_phc(),
            self.PHC_DELIVERY_LIMITS["no"],
        )
        descritivo = self._phc_trim(self.name, self.PHC_DELIVERY_LIMITS["name"])
        morada = self._phc_trim(self._pg_get_delivery_street_for_phc(), self.PHC_DELIVERY_LIMITS["street"])
        codpost = self._phc_trim(self.zip, self.PHC_DELIVERY_LIMITS["zip"])
        localidade = self._phc_trim(self.city, self.PHC_DELIVERY_LIMITS["city"])
        pais = self._pg_get_phc_country_code()
        contacto = self._phc_trim(
            self._pg_get_delivery_contacto_for_phc(),
            self.PHC_DELIVERY_LIMITS["pg_contacto_entrega"],
        )
        telefone = self._phc_trim(self.pg_telefone, self.PHC_DELIVERY_LIMITS["pg_telefone"])
        email = self._phc_trim(self.email, self.PHC_DELIVERY_LIMITS["email"])
        telemovel = self._phc_trim(self.phone, self.PHC_DELIVERY_LIMITS["phone"])

        xml_param = (
            f"<descritivo>{self._pg_escape_phc_xml(descritivo)}</descritivo>"
            f"<no>{self._pg_escape_phc_xml(parent_ref)}</no>"
            f"<morada>{self._pg_escape_phc_xml(morada)}</morada>"
            f"<codpost>{self._pg_escape_phc_xml(codpost)}</codpost>"
            f"<localidade>{self._pg_escape_phc_xml(localidade)}</localidade>"
            f"<pais>{self._pg_escape_phc_xml(pais)}</pais>"
            f"<contacto>{self._pg_escape_phc_xml(contacto)}</contacto>"
            f"<telefone>{self._pg_escape_phc_xml(telefone)}</telefone>"
            f"<email>{self._pg_escape_phc_xml(email, keep_apostrophe=True)}</email>"
            f"<telemovel>{self._pg_escape_phc_xml(telemovel)}</telemovel>"
        )
        _logger.info(
            "PHC delivery parameter XML built for partner %s | snapshot=%s | parameter_xml=%s",
            self.id,
            self._pg_get_phc_debug_snapshot(),
            self._pg_log_excerpt(xml_param),
        )
        return xml_param

    # --------------------------------------------------------------
    # SOAP RunCode call
    # --------------------------------------------------------------
    def _phc_run_code(self, code, parameter_xml):
        self.ensure_one()

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
                    "Preencha URL, utilizador e password na Configuração para a empresa ativa."
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

        _logger.info(
            "PHC RunCode request for partner %s | code=%s | ws_url=%s | snapshot=%s | parameter_xml=%s",
            self.id,
            code,
            ws_url,
            self._pg_get_phc_debug_snapshot(),
            self._pg_log_excerpt(parameter_xml),
        )

        try:
            resp = requests.post(
                ws_url,
                data=envelope.encode("utf-8"),
                headers=headers,
                timeout=30,
                verify=False,
            )
        except Exception as exc:
            _logger.exception("Erro a ligar ao PHC: %s", exc)
            raise UserError(_("Erro a ligar ao PHC: %s") % exc)

        _logger.info(
            "PHC RunCode raw HTTP response for partner %s | code=%s | status=%s | body=%s",
            self.id,
            code,
            resp.status_code,
            self._pg_log_excerpt(resp.text),
        )

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
            _logger.warning(
                "PHC RunCode SOAP fault for partner %s | code=%s | fault=%s | run_code_result=%s",
                self.id,
                code,
                fault_string,
                self._pg_log_excerpt(run_code_result),
            )
            raise UserError(_("PHC SOAP Fault: %s") % fault_string)

        _logger.info(
            "PHC RunCode parsed response for partner %s | code=%s | run_code_result=%s",
            self.id,
            code,
            self._pg_log_excerpt(run_code_result),
        )

        return response_text, run_code_result

    # --------------------------------------------------------------
    # Internal helpers used by auto-sync
    # --------------------------------------------------------------
    def _phc_push_create(self, raise_on_missing_ref=False):
        self.ensure_one()
        if self._phc_get_effective_ref():
            # O cliente já existe no PHC: passa a ser um UpdateCL e, por isso, sem NIF
            # no payload (o PHC mantém o NIF que já tem na ficha).
            self.with_context(skip_phc_auto_sync=True).sudo().write({"is_phc_synced": True})
            self.with_context(phc_autosync=True)._phc_push_update(
                raise_on_missing_ref=raise_on_missing_ref,
                old_vat=self.vat,
            )
            return

        self._phc_validate_sync_requirements()
        parameter_xml = self._phc_build_parameter_xml(for_update=False)

        try:
            resp_text, run_code_result = self._phc_run_code(PHC_SCRIPT_CODE, parameter_xml)
        except Exception as e:
            if not raise_on_missing_ref:
                _logger.exception("PHC create failed (autosync). Partner %s: %s", self.id, e)
                self.with_context(skip_phc_auto_sync=True).sudo().write(
                    {"phc_last_response": _("PHC error (autosync): %s") % str(e)}
                )
                return
            raise

        _logger.info(
            "PHC create completed for partner %s | run_code_result=%s",
            self.id,
            self._pg_log_excerpt(run_code_result),
        )

        vals = {"phc_last_response": resp_text}

        ref_value = self._phc_extract_ref_from_run_code_result(run_code_result)
        phc_message = self._phc_extract_message_from_run_code_result(run_code_result)
        _logger.info(
            "PHC create parse summary for partner %s | ref_value=%s | phc_message=%s | response_excerpt=%s",
            self.id,
            ref_value,
            self._pg_log_excerpt(phc_message, limit=250),
            self._pg_log_excerpt(resp_text),
        )
        if ref_value and not self._phc_get_effective_ref():
            vals.update(self._phc_get_effective_ref_write_vals(ref_value))

        if ref_value:
            vals["is_phc_synced"] = True

        self.with_context(skip_phc_auto_sync=True).sudo().write(vals)

        if raise_on_missing_ref and not ref_value:
            _logger.warning(
                "PHC create missing reference for partner %s | phc_message=%s | snapshot=%s | response_excerpt=%s",
                self.id,
                self._pg_log_excerpt(phc_message, limit=250),
                self._pg_get_phc_debug_snapshot(),
                self._pg_log_excerpt(resp_text),
            )
            if phc_message:
                raise UserError(
                    _(
                        "O PHC nao devolveu a referencia (Numero). Mensagem do PHC: %s. "
                        "Verifique a resposta em 'Ultima resposta PHC'."
                    )
                    % phc_message
                )
            if False and phc_message:
                raise UserError(
                    _(
                        "O PHC nÃ£o devolveu a referÃªncia (Numero). Mensagem do PHC: %s. "
                        "Verifique a resposta em 'Ãšltima resposta PHC'."
                    )
                    % phc_message
                )
            raise UserError(
                _("O PHC não devolveu a referência (Numero). Verifique a resposta em 'Última resposta PHC'.")
            )

    def _phc_push_delivery_create(self, raise_on_missing_ref=False):
        self.ensure_one()

        if self.is_phc_synced:
            return

        self._phc_validate_delivery_sync_requirements(self)
        parameter_xml = self._phc_build_delivery_parameter_xml()

        try:
            resp_text, run_code_result = self._phc_run_code(PHC_DELIVERY_SCRIPT_CODE, parameter_xml)
        except Exception as e:
            if not raise_on_missing_ref:
                _logger.exception("PHC delivery create failed (autosync). Partner %s: %s", self.id, e)
                self.with_context(skip_phc_auto_sync=True).sudo().write(
                    {"phc_last_response": _("PHC delivery error (autosync): %s") % str(e)}
                )
                return
            raise

        _logger.info(
            "PHC delivery create completed for partner %s | run_code_result=%s",
            self.id,
            self._pg_log_excerpt(run_code_result),
        )
        self.with_context(skip_phc_auto_sync=True).sudo().write(
            {
                "is_phc_synced": True,
                "phc_last_response": resp_text,
            }
        )

    def _phc_register_vat_lock_warning(self, msg, previous_response=""):
        """Registra, sem bloquear, uma recusa de NIF devolvida pelo PHC.

        Só é usado quando o UpdateCL foi disparado por uma gravação que não alterou
        o NIF: nesse caso o utilizador não tem nada para corrigir na ficha, logo a
        gravação no Odoo tem de persistir. A recusa fica visível em 'Última resposta
        PHC' e numa nota no registo (apenas na primeira ocorrência, para não encher
        o chatter em gravações seguidas).
        """
        self.ensure_one()

        _logger.warning(
            "PHC refused UpdateCL for partner %s with a VAT lock message even though this "
            "save did not change the VAT. Odoo data was kept; PHC was NOT updated. | msg=%s",
            self.id,
            msg,
        )

        self.with_context(skip_phc_auto_sync=True).sudo().write(
            {"phc_last_response": "%s\n\n%s" % (PHC_VAT_LOCK_MARKER, msg)}
        )

        if PHC_VAT_LOCK_MARKER not in (previous_response or ""):
            self.sudo().message_post(
                body=_(
                    "O PHC recusou a atualização deste cliente com a mensagem: "
                    "\"%s\"<br/><br/>"
                    "As alterações foram guardadas no Odoo mas <b>não</b> foram enviadas para o PHC. "
                    "Verifique o NIF da ficha no PHC (campo <code>ncont</code>) e a referência PHC "
                    "associada a este contacto."
                )
                % xml_escape(msg or "")
            )

    def _phc_push_update(self, raise_on_missing_ref=False, old_vat=None, include_vat=False):
        self.ensure_one()

        if not self._phc_get_effective_ref():
            if raise_on_missing_ref:
                raise UserError(_("Este cliente ainda não tem referência PHC (ref). Use 'PHC Sync' primeiro."))
            return

        previous_response = self.phc_last_response or ""

        self._phc_validate_sync_requirements()
        parameter_xml = self._phc_build_parameter_xml(for_update=True, include_vat=include_vat)

        try:
            resp_text, run_code_result = self._phc_run_code(PHC_SCRIPT_UPDATE_CODE, parameter_xml)
        except Exception as e:
            if not raise_on_missing_ref:
                _logger.exception("PHC update failed (autosync). Partner %s: %s", self.id, e)
                self.with_context(skip_phc_auto_sync=True).sudo().write(
                    {"phc_last_response": _("PHC error (autosync update): %s") % str(e)}
                )
                return
            raise

        _logger.info(
            "PHC update completed for partner %s | run_code_result=%s",
            self.id,
            self._pg_log_excerpt(run_code_result),
        )

        self.with_context(skip_phc_auto_sync=True).sudo().write({"phc_last_response": resp_text})

        msg = self._phc_extract_message_from_run_code_result(run_code_result)
        _logger.info(
            "PHC update parse summary for partner %s | phc_message=%s | response_excerpt=%s",
            self.id,
            self._pg_log_excerpt(msg, limit=250),
            self._pg_log_excerpt(resp_text),
        )
        if msg:
            msg_normalized = unicodedata.normalize("NFKD", msg).encode("ascii", "ignore").decode().lower()
            if any(snippet in msg.lower() or snippet in msg_normalized for snippet in PHC_VAT_LOCK_MSG_SNIPPETS):
                # Só bloqueia a gravação quando o NIF foi enviado de propósito, ou seja,
                # quando esta gravação alterou mesmo o NIF. Se o PHC recusar um update que
                # nem levava o NIF, a culpa não é do que o utilizador está a gravar:
                # registamos o aviso e deixamos o save do Odoo passar.
                if not include_vat:
                    self._phc_register_vat_lock_warning(msg, previous_response=previous_response)
                    return
                if old_vat is not None and (self.vat or "") != (old_vat or ""):
                    self.with_context(skip_phc_auto_sync=True).sudo().write({"vat": old_vat})
                raise UserError(_(msg))

    def _phc_auto_sync_after_save(self, vals, old_vat_by_id=None, vat_changed_ids=None):
        """Auto-sync PHC no fim do create/write.

        `vat_changed_ids` traz os ids em que esta operação alterou mesmo o NIF; só
        nesses é que o UpdateCL leva `ncont`/`pncont` no payload (ver
        `_phc_build_parameter_xml`).
        """
        if self.env.context.get("skip_phc_auto_sync"):
            return

        ignored_keys = {"phc_last_response", "is_phc_synced", "responsavel_interno"}
        if set(vals.keys()).issubset(ignored_keys):
            return

        if self.env.context.get("import_file"):
            for rec in self:
                has_effective_ref = bool(rec._phc_get_effective_ref())
                if rec._pg_is_phc_delivery_contact():
                    continue
                if not rec._pg_is_phc_company_contact():
                    if rec.is_phc_synced:
                        rec.with_context(skip_phc_auto_sync=True).sudo().write({"is_phc_synced": False})
                    continue
                if rec.is_phc_synced and not has_effective_ref:
                    rec.with_context(skip_phc_auto_sync=True).sudo().write({"is_phc_synced": False})
                elif has_effective_ref and not rec.is_phc_synced:
                    rec.with_context(skip_phc_auto_sync=True).sudo().write({"is_phc_synced": True})
            return

        for rec in self:
            has_effective_ref = bool(rec._phc_get_effective_ref())

            if rec._pg_is_phc_delivery_contact():
                if rec.is_phc_synced:
                    continue

                block_reasons = rec._get_phc_sync_block_reasons()
                if block_reasons:
                    rec._phc_mark_sync_blocked(block_reasons)
                    continue

                rec.with_context(phc_autosync=True)._phc_push_delivery_create(
                    raise_on_missing_ref=False,
                )
                continue

            if not rec._pg_is_phc_company_contact():
                if rec.is_phc_synced:
                    rec.with_context(skip_phc_auto_sync=True).sudo().write({"is_phc_synced": False})
                continue

            only_non_internal_users = bool(rec.user_ids) and not rec.user_ids.filtered(lambda u: u._is_internal())
            if only_non_internal_users:
                if rec.is_phc_synced and not has_effective_ref:
                    rec.with_context(skip_phc_auto_sync=True).sudo().write({"is_phc_synced": False})
                continue

            if not (rec.is_phc_synced or has_effective_ref):
                continue

            block_reasons = rec._get_phc_sync_block_reasons()
            if block_reasons:
                rec._phc_mark_sync_blocked(block_reasons)
                continue

            if has_effective_ref and not rec.is_phc_synced:
                rec.with_context(skip_phc_auto_sync=True).sudo().write({"is_phc_synced": True})

            old_vat = (old_vat_by_id or {}).get(rec.id)
            rec.with_context(phc_autosync=True)._phc_push_update(
                raise_on_missing_ref=False,
                old_vat=old_vat,
                include_vat=rec.id in (vat_changed_ids or set()),
            )

    # --------------------------------------------------------------
    # create/write hooks (AUTO SYNC on save)
    # + VAT change lock if partner has invoices
    # --------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        records._apply_phc_incoming_sync()
        records._apply_phc_outgoing_sync()

        for rec, vals in zip(records, vals_list):
            # Numa criação o NIF está a ser definido agora, logo faz sentido enviá-lo.
            rec._phc_auto_sync_after_save(
                vals,
                old_vat_by_id=None,
                vat_changed_ids={rec.id} if (vals.get("vat") or "").strip() else None,
            )

        return records

    def write(self, vals):
        old_vat_by_id = {}
        vat_changed_ids = set()
        phc_company_enabled = (
            ("is_company" in vals and vals.get("is_company"))
            or ("company_type" in vals and vals.get("company_type") == "company")
        )
        if "vat" in vals:
            new_vat = (vals.get("vat") or "").strip()
            for rec in self:
                old_vat_by_id[rec.id] = rec.vat
                if (rec.vat or "").strip() != new_vat:
                    vat_changed_ids.add(rec.id)

        if vat_changed_ids and not self._pg_is_native_import():
            for rec in self.filtered(lambda partner: partner.id in vat_changed_ids):
                if rec._has_posted_customer_documents():
                    raise ValidationError(
                        _(
                            "Não é permitido alterar o NIF deste cliente porque já existem faturas/notas de crédito "
                            "validadas no Odoo."
                        )
                    )

        res = super().write(vals)

        if any(k in vals for k in ("x_studio_salesperson_id_1", "x_studio_country_code")) or phc_company_enabled:
            self._apply_phc_incoming_sync()
        if any(k in vals for k in ("user_id", "country_id")) or phc_company_enabled:
            self._apply_phc_outgoing_sync()

        self._phc_auto_sync_after_save(
            vals,
            old_vat_by_id=old_vat_by_id,
            vat_changed_ids=vat_changed_ids,
        )
        return res

    # --------------------------------------------------------------
    # Manual Buttons
    # --------------------------------------------------------------
    def _pg_get_manual_action_partners(self):
        partners = self
        if not partners and self.env.context.get("active_model") == "res.partner":
            partners = self.browse(self.env.context.get("active_ids", []))
        if not partners:
            raise UserError(_("Selecione pelo menos um contacto para sincronizar com o PHC."))
        return partners

    @staticmethod
    def _pg_raise_manual_action_error(partner, error, action_label):
        raise UserError(
            _("Falha na %(action)s PHC para o contacto '%(partner)s':\n\n%(error)s")
            % {
                "action": action_label,
                "partner": partner.display_name,
                "error": str(error),
            }
        ) from error

    @staticmethod
    def _pg_format_blocked_partners_message(blocked, header):
        sections = [header]
        for partner, reasons in blocked:
            sections.append(
                _("Contacto '%(partner)s':\n%(reasons)s")
                % {
                    "partner": partner.display_name,
                    "reasons": "\n\n".join(reasons),
                }
            )
        return "\n\n".join(sections)

    def action_sync_phc(self):
        partners = self._pg_get_manual_action_partners()

        # Validate every selected partner BEFORE pushing any of them to PHC.
        # This avoids a partial success where some partners are sync'd to PHC
        # and then a popup raises (rolling back local writes only — leaving
        # PHC and Odoo out of sync).
        blocked = []
        for partner in partners:
            reasons = partner._get_phc_sync_block_reasons()
            if reasons:
                blocked.append((partner, reasons))

        if blocked:
            header = _(
                "Sincronização com o PHC bloqueada para %s contacto(s). Corrija os campos indicados:"
            ) % len(blocked)
            raise UserError(self._pg_format_blocked_partners_message(blocked, header))

        synced_count = 0
        for partner in partners:
            if partner._pg_is_phc_delivery_contact():
                if partner.is_phc_synced:
                    synced_count += 1
                    continue
                try:
                    partner.with_context(phc_autosync=True)._phc_push_delivery_create(raise_on_missing_ref=True)
                except Exception as error:
                    self._pg_raise_manual_action_error(partner, error, _("sincronização"))
            elif partner._phc_should_update():
                try:
                    # Sem `include_vat`: um push manual não altera o NIF, e enviá-lo
                    # faria o PHC recusar a ficha toda quando já tem documentos
                    # certificados emitidos.
                    partner.with_context(phc_autosync=True)._phc_push_update(
                        raise_on_missing_ref=True,
                        old_vat=partner.vat,
                    )
                except Exception as error:
                    self._pg_raise_manual_action_error(partner, error, _("sincronização"))
            else:
                try:
                    partner.with_context(phc_autosync=True)._phc_push_create(raise_on_missing_ref=True)
                except Exception as error:
                    self._pg_raise_manual_action_error(partner, error, _("sincronização"))
            synced_count += 1

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Sincronização PHC"),
                "message": _(
                    "Criação/Sincronização no PHC concluída para %s contacto(s). "
                    "Consulte 'Última resposta PHC' para detalhes."
                ) % synced_count,
                "sticky": False,
            },
        }

    def action_update_phc(self):
        partners = self._pg_get_manual_action_partners()

        blocked = []
        for partner in partners:
            reasons = partner._get_phc_sync_block_reasons()
            if reasons:
                blocked.append((partner, reasons))

        if blocked:
            header = _(
                "Atualização no PHC bloqueada para %s contacto(s). Corrija os campos indicados:"
            ) % len(blocked)
            raise UserError(self._pg_format_blocked_partners_message(blocked, header))

        synced_count = 0
        for partner in partners:
            try:
                # Sem `include_vat`: ver nota em `_phc_build_parameter_xml`. Uma
                # correção de NIF é enviada pela própria gravação do campo.
                partner.with_context(phc_autosync=True)._phc_push_update(
                    raise_on_missing_ref=True,
                    old_vat=partner.vat,
                )
            except Exception as error:
                self._pg_raise_manual_action_error(partner, error, _("atualização"))
            synced_count += 1

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Atualização PHC"),
                "message": _(
                    "Atualização no PHC concluída para %s contacto(s). "
                    "Consulte 'Última resposta PHC' para detalhes."
                ) % synced_count,
                "sticky": False,
            },
        }
