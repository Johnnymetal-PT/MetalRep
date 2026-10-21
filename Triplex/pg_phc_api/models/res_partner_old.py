# -*- coding: utf-8 -*-
"""
Implementacao legacy da sincronizacao de parceiros com PHC.

Modulo: pg_phc_api.
Ficheiro: pg_phc_api\models\res_partner_old.py.
Nota: manter apenas para referencia e retrocompatibilidade; o fluxo atual esta noutro ficheiro.
"""

# CÓDIGO MORTO: versão antiga do conector de clientes PHC. NÃO é importado em
# models/__init__.py, logo não é carregado. O código ativo está em res_partner.py.
# Mantido apenas por histórico.
import logging
import re
import xml.etree.ElementTree as ET

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

# Scripts PHC
PHC_SCRIPT_CODE = "CriaCL"
PHC_SCRIPT_UPDATE_CODE = "UpdateCL"


class ResUsers(models.Model):
    _inherit = "res.users"

    # This MUST exist in DB (your error shows it doesn't).
    # Declaring it here will create the column on module upgrade.
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
        "x_studio_salesperson_id_1": 4,  # PHC salesperson number (vendedornr)
        "property_payment_term_id": 55,
        "x_studio_tabela_precos": 1,
        "responsavel_interno": 30,
        "ref": 20,  # usado como <no> no update
    }

    # -----------------------------
    # PHC toggle like invoices
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

    x_studio_country_code = fields.Char(
        string="Código País PHC",
        size=PHC_LIMITS["x_studio_country_code"],
        required=True,
        help="Código de país PHC (pncont). Ex: PT",
    )

    # Partner field is PHC salesperson number (vendedornr), NOT res.users.id.
    x_studio_salesperson_id_1 = fields.Integer(
        string="Vendedor PHC (nº)",
        required=True,
        help="Número do vendedor no PHC (vendedornr). Vai procurar o utilizador cujo res.users.x_studio_salesperson_id_1 seja igual.",
        index=True,
    )

    # campo antigo (mantive como tens)
    x_studio_salesperson_id = fields.Integer(
        string="Vendedor PHC old",
        required=True,
        help="Número do vendedor no PHC (vendedornr) old",
    )

    x_studio_tabela_precos = fields.Selection(
        selection=[("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5")],
        string="Tabela de Preços (PHC)",
        required=True,
        help="Tabela de preços PHC (tabprecost).",
    )

    responsavel_interno = fields.Char(
        string="Responsável Interno (PHC)",
        size=PHC_LIMITS["responsavel_interno"],
        required=True,
        help="Responsável interno (respint).",
    )

    # --------------------------------------------------------------
    # Utils
    # --------------------------------------------------------------
    @staticmethod
    def _phc_trim(value, limit):
        if not value:
            return ""
        return str(value)[:limit]

    def _get_user_by_phc_salesperson_nr(self, salesperson_nr):
        """Find a single user by PHC salesperson number stored on res.users.x_studio_salesperson_id_1."""
        if not salesperson_nr:
            return self.env["res.users"]
        return self.env["res.users"].sudo().search(
            [("x_studio_salesperson_id_1", "=", int(salesperson_nr))],
            limit=1,
        )

    # --------------------------------------------------------------
    #  AUTOMATIONS EMBEDDED (Auto 1,2,3,4)
    # --------------------------------------------------------------
    def _apply_phc_incoming_sync(self):
        """
        PHC -> Odoo
        - partner.x_studio_salesperson_id_1 (PHC salesperson nr) -> user_id via users.x_studio_salesperson_id_1
        - x_studio_country_code (PT, ES, ...) -> country_id (set if empty OR different)
        """
        if self.env.context.get("skip_phc_incoming_sync"):
            return

        for rec in self:
            vals = {}

            # Auto 1) Salesperson nr (PHC) -> user_id
            if rec.x_studio_salesperson_id_1:
                user = rec._get_user_by_phc_salesperson_nr(rec.x_studio_salesperson_id_1)
                if user and rec.user_id.id != user.id:
                    vals["user_id"] = user.id

            # Auto 2) Country code from PHC -> country_id
            code = (rec.x_studio_country_code or "").strip().upper()
            if code:
                current_country_code = (
                    (rec.country_id.code or "").strip().upper()
                    if rec.country_id
                    else ""
                )
                if not rec.country_id or current_country_code != code:
                    country = self.env["res.country"].sudo().search(
                        ["|", ("code", "=", code), ("name", "=", code)],
                        limit=1,
                    )
                    if country:
                        vals["country_id"] = country.id

            if vals:
                rec.sudo().with_context(skip_phc_outgoing_sync=True).write(vals)

    def _apply_phc_outgoing_sync(self):
        """
        Odoo -> PHC coherence
        - user_id -> partner.x_studio_salesperson_id_1 using users.x_studio_salesperson_id_1
        - country_id -> x_studio_country_code (ISO code)
        """
        if self.env.context.get("skip_phc_outgoing_sync"):
            return

        for rec in self:
            vals = {}

            # Auto 4) user_id -> partner salesperson nr
            new_sales_nr = rec.user_id.x_studio_salesperson_id_1 if rec.user_id else 0
            current_sales_nr = rec.x_studio_salesperson_id_1 or 0
            if (current_sales_nr or 0) != (new_sales_nr or 0):
                vals["x_studio_salesperson_id_1"] = new_sales_nr or 0

            # Auto 3) country_id -> x_studio_country_code
            if rec.country_id and rec.country_id.code:
                new_code = (rec.country_id.code or "").strip().upper()
                current_code = (rec.x_studio_country_code or "").strip().upper()
                if new_code and current_code != new_code:
                    vals["x_studio_country_code"] = new_code

            if vals:
                rec.sudo().with_context(skip_phc_incoming_sync=True).write(vals)

    # --------------------------------------------------------------
    # Immediate UI sync (not only on save)
    # --------------------------------------------------------------
    @api.onchange("x_studio_salesperson_id_1")
    def _onchange_phc_salesperson_id_1(self):
        """
        Partner salesperson nr changed -> set user_id via users.x_studio_salesperson_id_1
        """
        for rec in self:
            if rec.x_studio_salesperson_id_1:
                user = rec._get_user_by_phc_salesperson_nr(rec.x_studio_salesperson_id_1)
                if user:
                    rec.user_id = user

    @api.onchange("user_id")
    def _onchange_user_id_to_phc_salesperson_id_1(self):
        """
        user_id changed -> set partner salesperson nr from user.x_studio_salesperson_id_1
        """
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
                (rec.country_id.code or "").strip().upper()
                if rec.country_id
                else ""
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
    # Constraints / Validation (FIXED FOR DUPLICATE)
    # --------------------------------------------------------------
    @api.constrains(
        "vat",
        "name",
        "street",
        "zip",
        "city",
        "email",
        "phone",
        "x_studio_country_code",
        "x_studio_salesperson_id_1",
        "x_studio_tabela_precos",
        "responsavel_interno",
        "country_id",
        "property_payment_term_id",
    )
    def _check_phc_requirements(self):
        for partner in self:
            must_validate_for_phc = bool(
                partner.is_phc_synced
                or partner.ref
                or self.env.context.get("phc_autosync")
            )

            if not must_validate_for_phc:
                continue

            missing = []
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
                "x_studio_tabela_precos",
                "responsavel_interno",
            ]

            for fname in required_fields:
                if not getattr(partner, fname):
                    missing.append(fname)

            if not partner.property_payment_term_id:
                missing.append("property_payment_term_id")

            if missing:
                raise ValidationError(
                    _("Os seguintes campos PHC são obrigatórios: %s")
                    % ", ".join(missing)
                )

            if partner.country_id and partner.country_id.code == "PT":
                if partner.zip and not re.match(r"^\d{4}-\d{3}$", partner.zip):
                    raise ValidationError(
                        _("O código postal português deve estar no formato 1234-123.")
                    )

            if partner.x_studio_salesperson_id_1 and partner.x_studio_salesperson_id_1 > 9999:
                raise ValidationError(
                    _("O número do vendedor PHC deve ter no máximo 4 dígitos.")
                )

            for fname, limit in partner.PHC_LIMITS.items():
                if fname == "x_studio_salesperson_id_1":
                    continue
                if fname == "property_payment_term_id":
                    value = partner.property_payment_term_id.name or ""
                else:
                    value = getattr(partner, fname) or ""
                if len(str(value)) > limit:
                    raise ValidationError(
                        _("O campo %s excede o limite de %s caracteres.")
                        % (fname, limit)
                    )

    # --------------------------------------------------------------
    # Build CDATA parameter XML
    # --------------------------------------------------------------
    def _phc_build_parameter_xml(self, for_update=False):
        self.ensure_one()

        pncont = self._phc_trim(self.x_studio_country_code, self.PHC_LIMITS["x_studio_country_code"])
        ncont = self._phc_trim(self.vat, self.PHC_LIMITS["vat"])
        nome = self._phc_trim(self.name, self.PHC_LIMITS["name"])
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

        respint = self._phc_trim(self.responsavel_interno, self.PHC_LIMITS["responsavel_interno"])
        tabprecost = self._phc_trim(self.x_studio_tabela_precos, self.PHC_LIMITS["x_studio_tabela_precos"])

        no_tag = ""
        if for_update:
            if not self.ref:
                raise UserError(
                    _("Para atualizar no PHC é obrigatório ter a referência PHC (ref).")
                )
            no_value = self._phc_trim(self.ref, self.PHC_LIMITS["ref"])
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
            f"<respint>{respint}</respint>"
            f"<tabprecost>{tabprecost}</tabprecost>"
        )
        return xml_param

    # --------------------------------------------------------------
    # SOAP RunCode call
    # --------------------------------------------------------------
    def _phc_run_code(self, code, parameter_xml):
        self.ensure_one()

        u = self.env.user
        ws_url = (u.phc_api_base_url or "").strip()
        phc_user = (u.phc_api_user or "").strip()
        phc_password = (u.phc_api_password or "").strip()

        if not ws_url or not phc_user or not phc_password:
            raise UserError(
                _(
                    "Credenciais PHC em falta. "
                    "Preencha URL, utilizador e password na tab 'Credenciais PHC' do seu utilizador."
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
    def _phc_push_create(self):
        """Send CriaCL for this partner and mark synced on success."""
        self.ensure_one()
        parameter_xml = self._phc_build_parameter_xml(for_update=False)
        resp_text, run_code_result = self._phc_run_code(PHC_SCRIPT_CODE, parameter_xml)

        vals = {"phc_last_response": resp_text}

        if run_code_result:
            match = re.search(r"(\d+)\s*$", run_code_result)
            if match and not self.ref:
                vals["ref"] = match.group(1)

        vals["is_phc_synced"] = True
        self.with_context(skip_phc_auto_sync=True).sudo().write(vals)

    def _phc_push_update(self):
        """Send UpdateCL for this partner."""
        self.ensure_one()
        parameter_xml = self._phc_build_parameter_xml(for_update=True)
        resp_text, _run_code_result = self._phc_run_code(PHC_SCRIPT_UPDATE_CODE, parameter_xml)

        self.with_context(skip_phc_auto_sync=True).sudo().write(
            {"phc_last_response": resp_text}
        )

    def _phc_auto_sync_after_save(self, vals):
        """
        Called after create/write.
        False -> create in PHC then set True.
        True  -> update in PHC.
        """
        if self.env.context.get("skip_phc_auto_sync"):
            return

        ignored_keys = {"phc_last_response", "is_phc_synced"}
        if set(vals.keys()).issubset(ignored_keys):
            return

        for rec in self:
            if not rec.is_phc_synced:
                rec.with_context(phc_autosync=True)._phc_push_create()
            else:
                rec.with_context(phc_autosync=True)._phc_push_update()

    # --------------------------------------------------------------
    # create/write hooks (AUTO SYNC on save)
    # --------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        # coherence automations
        records._apply_phc_incoming_sync()
        records._apply_phc_outgoing_sync()

        # auto push to PHC (create)
        for rec, vals in zip(records, vals_list):
            rec._phc_auto_sync_after_save(vals)

        return records

    def write(self, vals):
        res = super().write(vals)

        # coherence automations
        if any(k in vals for k in ("x_studio_salesperson_id_1", "x_studio_country_code")):
            self._apply_phc_incoming_sync()
        if any(k in vals for k in ("user_id", "country_id")):
            self._apply_phc_outgoing_sync()

        # auto push to PHC
        self._phc_auto_sync_after_save(vals)

        return res

    # --------------------------------------------------------------
    # Manual Buttons (still work)
    # --------------------------------------------------------------
    def action_sync_phc(self):
        for partner in self:
            partner.with_context(phc_autosync=True)._phc_push_create()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("PHC Sync"),
                "message": _("Criação/Sync no PHC concluída. Consulte 'Última resposta PHC'."),
                "sticky": False,
            },
        }

    def action_update_phc(self):
        for partner in self:
            partner.with_context(phc_autosync=True)._phc_push_update()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("PHC Update"),
                "message": _("Atualização no PHC concluída. Consulte 'Última resposta PHC'."),
                "sticky": False,
            },
        }
