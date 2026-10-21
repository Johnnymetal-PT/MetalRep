# -*- coding: utf-8 -*-
# Ready-to-paste full invoice model + connection (Odoo 17.0)
# Fixes in this version:
# - Force decimal "." in all numeric values sent to PHC
# - Downpayment doctype = 1
# - Downpayment invoices call CriaFTAD with its own parameter set
# - CriaFTAD sends <tabiva>
# - x_studio_tipo_de_artigo is RELATED to product.type (consu/service/combo)
# - SOAP <code> is injected dynamically (CriaFT vs CriaFTAD)
# - When syncing a DOWNPAYMENT (CriaFTAD), store returned "Ano" + "FT_Adiantamento" on that invoice
# - When syncing a FINAL invoice (CriaFT) that contains negative downpayment lines:
#     - Do NOT send "Down Payments" section nor any downpayment lines
#     - Do NOT reduce/adjust product lines (send full/gross lines)
#     - Send downpayment references as: adano1/adnum1 ... adano10/adnum10 (from referenced downpayment invoices)
# - NEW (ANTI DUPLICATION):
#     - If a downpayment invoice already has PHC Ano/FT_Adiantamento, do NOT call CriaFTAD again
#     - If an invoice is already synced, do not sync again (unless forced via context phc_force_resync=True)
#     - _post() only syncs moves that are not already synced
# - NEW (PHC DESCRIPTION WRAP + NOTE LINES INLINE):
#     - PHC design max = 60 chars
#     - If a product line's description exceeds 60, send continuation lines right after it:
#         * <ref></ref>
#         * qtd=0 / prunit=0 / desc1=0
#         * <tabiva></tabiva>  (EMPTY! this is what fixed your “blank line treated as item” problem)
#     - Odoo line_note is sent as blank PHC lines IN THE SAME POSITION as in Odoo
#     - line_section is ignored

import ast
import logging
import re
import requests
from xml.sax.saxutils import escape as xml_escape

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from lxml import etree
from odoo.tools import misc
from odoo.tools.float_utils import float_round

_logger = logging.getLogger(__name__)


# ============================================================
#  PHC CONNECTION
# ============================================================
class PHCConnection(object):

    PHC_REF_MAP = {
        "product": "MERCADORIAS",
        "service": "SERVIÇO",
        "consu": "CONSUMIVEL",
        "combo": "COMBO",  # safe extra mapping if you have combo in some DBs
    }

    PHC_DESIGN_MAX = 60

    def __init__(self, url, username, password, verify_ssl=False):
        if not url or not username or not password:
            raise Exception(_("PHC connection parameters are missing."))

        self.url = url
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.headers = self._set_headers()

    def _set_headers(self):
        return {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "http://www.phc.pt/RunCode",
        }

    def _get_template(self, xml_filename):
        return etree.parse(
            misc.file_path("pg_phc_api_integration/api/%s" % xml_filename)
        )

    def _set_template_details(self, move, phc_code, xml_filename="send_invoice.xml"):
        """
        Loads the given XML template and injects:
          - username/password
          - code (CriaFT / CriaFTAD / CriaFTGT)
          - parameter CDATA
        """
        tree = self._get_template(xml_filename)
        root = tree.getroot()

        if phc_code == "CriaFTAD":
            move_content = self._prepare_downpayment_parameter(move)
        elif phc_code == "CriaFTGT":
            move_content = self._prepare_delivery_parameter(move)
        else:
            move_content = self._prepare_move_parameter(move)

        for parent_node in root:
            for node in parent_node:
                for sub_node in node:
                    if not isinstance(sub_node.tag, str):
                        continue

                    if "userName" in sub_node.tag:
                        sub_node.text = self.username
                    elif "password" in sub_node.tag:
                        sub_node.text = self.password
                    elif "code" in sub_node.tag:
                        sub_node.text = phc_code
                    elif "parameter" in sub_node.tag:
                        sub_node.text = etree.CDATA(move_content)

        return etree.tostring(tree, encoding="utf-8"), move_content

    # -----------------------------------------------------------------
    # Helpers enforcing limits + decimal dot
    # -----------------------------------------------------------------
    @staticmethod
    def _sanitize_text(value, max_len):
        # Truncate to PHC field length first (counts user-visible chars),
        # then XML-escape so chars like & < > don't break PHC's LoadXml on
        # the <parameter> content. PHC decodes the entities back on parse,
        # so the stored value still respects max_len.
        value = (value or "").strip()
        return xml_escape(value[:max_len])

    @staticmethod
    def _sanitize_numeric(value, precision, max_len):
        """
        Formats numeric with given precision; forces decimal "."; truncates length.
        """
        safe_value = float_round(value or 0.0, precision_digits=precision)
        txt = f"{safe_value:.{precision}f}".strip()
        txt = txt.replace(",", ".")
        return txt[:max_len]

    @staticmethod
    def _digits_only(value, max_len):
        """
        Keep only digits and trim. Useful for numeric(10,0), etc.
        """
        txt = re.sub(r"\D", "", (value or ""))
        return txt[:max_len]

    @staticmethod
    def _get_partner_phc_ref(move):
        """
        Resolve partner PHC reference in the invoice company context.
        Uses partner custom logic when available, with safe fallback to ref.
        """
        partner = move.partner_id.with_company(move.company_id) if move.partner_id else move.partner_id
        if not partner:
            return ""
        if hasattr(partner, "_phc_get_effective_ref"):
            return (partner._phc_get_effective_ref() or "").strip()
        return (partner.ref or "").strip()

    @staticmethod
    def _get_chain_value(record, chain):
        current = record
        for field_name in chain.split("."):
            if not current or field_name not in getattr(current, "_fields", {}):
                return ""
            current = current[field_name]

        if hasattr(current, "_name"):
            return current
        return current or ""

    @staticmethod
    def _split_design(text, max_len):
        """
        Split text into chunks <= max_len.
        Prefer splitting on spaces; fallback to hard split.
        """
        txt = (text or "").strip()
        if not txt:
            return [""]

        parts = []
        while len(txt) > max_len:
            cut = txt.rfind(" ", 0, max_len + 1)
            if cut <= 0:
                cut = max_len
            parts.append(txt[:cut].rstrip())
            txt = txt[cut:].lstrip()
        if txt:
            parts.append(txt)
        return parts or [""]

    @staticmethod
    def _split_design_with_newlines(text, max_len):
        """
        Split text into chunks <= max_len while preserving line breaks.
        Each newline starts a new PHC line. Internal blank lines are kept
        (as empty entries) so double line breaks survive into PHC; leading
        and trailing blanks are trimmed.
        """
        txt = (text or "").replace("\r\n", "\n").replace("\r", "\n")
        if not txt:
            return [""]

        parts = []
        for raw_line in txt.split("\n"):
            line = raw_line.strip()
            if not line:
                parts.append("")
                continue
            parts.extend(PHCConnection._split_design(line, max_len))

        while parts and parts[0] == "":
            parts.pop(0)
        while parts and parts[-1] == "":
            parts.pop()

        return parts or [""]

    def _append_blank_line(self, move_content, design_value, zero_qtd, zero_prunit, zero_desc1):
        """
        A PHC "blank" continuation/note line:
          <ref></ref>
          <design>...</design>
          qty/price/discount are zero
          <tabiva></tabiva> is EMPTY (critical!)

        If design ends up empty (e.g. blank line from a \n\n in the Odoo
        description), substitute a single space. PHC's CriaFT mishandles
        rows with totally empty <design> + qty=0 + tabiva=empty — it
        corrupts the parser state and adjacent product items get
        misclassified (seen in FT/196 and FT/199 with double-break
        descriptions). A single space renders blank in PHC but survives.
        """
        if not design_value:
            # Non-breaking space — PHC's CriaFT trims regular whitespace, which
            # turns a blank continuation back into the parser-corrupting "all
            # empty" row. \xa0 is not XML whitespace so it survives intact.
            design_value = "\xa0"
        return move_content + (
            f"<ref></ref>"
            f"<design>{design_value}</design>"
            f"<qtd>{zero_qtd}</qtd>"
            f"<prunit>{zero_prunit}</prunit>"
            f"<desc1>{zero_desc1}</desc1>"
            f"<tabiva></tabiva>"
        )

    def _append_blank_delivery_line(self, move_content, design_value, zero_qtd):
        if not design_value:
            # Non-breaking space — PHC's CriaFT trims regular whitespace, which
            # turns a blank continuation back into the parser-corrupting "all
            # empty" row. \xa0 is not XML whitespace so it survives intact.
            design_value = "\xa0"
        return move_content + (
            f"<ref></ref>"
            f"<design>{design_value}</design>"
            f"<qtd>{zero_qtd}</qtd>"
            f"<tabiva></tabiva>"
        )

    # -----------------------------------------------------------------
    #  CriaFT (normal/final invoice) parameter builder
    # -----------------------------------------------------------------
    def _prepare_move_parameter(self, move):
        """
        - Keeps invoice line order as in move.invoice_line_ids (so notes appear exactly where they are in Odoo)
        - Sends line_note as blank PHC lines inline
        - Ignores line_section
        - If final invoice has negative downpayment lines, skips ALL downpayment item lines (notes still go through)
        - Wraps long descriptions into blank continuation lines with EMPTY tabiva
        """
        partner_ref = self._get_partner_phc_ref(move)
        if not partner_ref:
            raise ValidationError(_("Partner has no PHC number (ref). Sync client first."))

        no_value = self._digits_only(partner_ref, 10)
        if not no_value:
            raise ValidationError(_("Partner PHC reference must be numeric."))

        doctype = int(getattr(move, "x_studio_doctype_phc", 1) or 1)
        doctype_value = self._sanitize_text(str(doctype), 1)

        move_content = f"<no>{no_value}</no><doctype>{doctype_value}</doctype>"

        # Inject downpayment references (if any) as adano/adnum tags
        dp_refs = move.env.context.get("phc_dp_refs") or []
        for idx in range(1, 11):
            if idx <= len(dp_refs):
                ano = self._digits_only(dp_refs[idx - 1].get("ano"), 4)
                num = self._digits_only(dp_refs[idx - 1].get("num"), 10)
            else:
                ano = ""
                num = ""
            move_content += f"<adano{idx}>{ano}</adano{idx}>"
            move_content += f"<adnum{idx}>{num}</adnum{idx}>"

        # Lines source (keep original order)
        lines = move.invoice_line_ids
        if not lines:
            lines = move.line_ids.filtered(
                lambda l:
                    not l.tax_line_id
                    and (l.product_id or (l.quantity not in (0, None)))
                    and (not l.account_id or l.account_id.account_type not in ("asset_receivable", "liability_payable"))
            )

        if not lines:
            raise ValidationError(_("Invoice has no lines to send to PHC."))

        # Determine if this is a "final invoice with negative downpayment lines"
        has_negative_dp = bool(
            lines.filtered(
                lambda l:
                    getattr(l, "display_type", False) not in ("line_section", "line_note")
                    and getattr(l, "is_downpayment", False)
                    and (l.quantity or 0.0) < 0
            )
        )

        zero_qtd = self._sanitize_numeric(0.0, precision=3, max_len=12)
        zero_prunit = self._sanitize_numeric(0.0, precision=6, max_len=19)
        zero_desc1 = self._sanitize_numeric(0.0, precision=2, max_len=6)

        sent_anything = False

        for line in lines:
            display_type = getattr(line, "display_type", False)

            # 1) Skip sections entirely
            if display_type == "line_section":
                continue

            # 2) Notes: send as blank PHC lines IN PLACE
            if display_type == "line_note":
                note_text = (line.name or "").strip()
                note_parts = self._split_design_with_newlines(note_text, self.PHC_DESIGN_MAX)
                emitted_note = False
                for part in note_parts:
                    part_value = self._sanitize_text(part, self.PHC_DESIGN_MAX)
                    move_content = self._append_blank_line(
                        move_content, part_value, zero_qtd, zero_prunit, zero_desc1
                    )
                    sent_anything = True
                    emitted_note = True
                if emitted_note:
                    move_content = self._append_blank_line(
                        move_content, "", zero_qtd, zero_prunit, zero_desc1
                    )
                continue

            # 3) Normal invoice lines:
            # If final invoice has negative downpayment lines, skip all downpayment lines
            if has_negative_dp and getattr(line, "is_downpayment", False):
                continue

            # Ref mapping (prefer related type if present)
            artigo = (getattr(line, "x_studio_tipo_de_artigo", False) or "").strip()
            if artigo:
                ref_src = artigo
            else:
                ref_src = (
                    line.product_id.default_code
                    or line.product_id.name
                    or line.name
                )

            ref_src = (ref_src or "").strip()
            ref_mapped = self.PHC_REF_MAP.get(ref_src.lower(), ref_src)
            ref_value = self._sanitize_text(ref_mapped, 18)
            if not ref_value:
                raise ValidationError(_("Each invoice line must have a PHC reference."))

            # Split design for main + continuation lines
            design_full = (line.name or "").strip()
            design_parts = self._split_design_with_newlines(design_full, self.PHC_DESIGN_MAX)
            design_first = self._sanitize_text(design_parts[0], self.PHC_DESIGN_MAX)

            qtd_value = self._sanitize_numeric(line.quantity, precision=3, max_len=12)
            prunit_value = self._sanitize_numeric(line.price_unit or 0.0, precision=6, max_len=19)
            desc1_value = self._sanitize_numeric(line.discount or 0.0, precision=2, max_len=6)

            # IMPORTANT: keep the normal line's tabiva as before (NOT empty)
            tabiva_value = "0"
            if line.tax_ids:
                tax = line.tax_ids[0]
                if hasattr(tax, "x_studio_n_tabela_phc_1") and tax.x_studio_n_tabela_phc_1:
                    tabiva_value = self._sanitize_text(str(int(tax.x_studio_n_tabela_phc_1)), 1)
                else:
                    tabiva_value = self._sanitize_text(str(int(tax.amount or 0)), 1)

            # Main (real) line
            move_content += (
                f"<ref>{ref_value}</ref>"
                f"<design>{design_first}</design>"
                f"<qtd>{qtd_value}</qtd>"
                f"<prunit>{prunit_value}</prunit>"
                f"<desc1>{desc1_value}</desc1>"
                f"<tabiva>{tabiva_value}</tabiva>"
            )
            sent_anything = True

            # Continuation blank lines immediately after (wrapped chunks +
            # internal \n\n blanks from _split_design_with_newlines).
            # NOTE: do NOT emit an auto-separator at the end of the block —
            # PHC's CriaFT was absorbing the next product's <ref> as a
            # continuation, causing subsequent products to render with 0 qty/
            # price. If the user wants visual spacing between products,
            # they put a trailing blank line in the description itself
            # (preserved as an internal "" entry by _split_design_with_newlines
            # — leading/trailing blanks ARE stripped to keep this opt-in).
            for part in design_parts[1:]:
                part_value = self._sanitize_text(part, self.PHC_DESIGN_MAX)
                move_content = self._append_blank_line(
                    move_content, part_value, zero_qtd, zero_prunit, zero_desc1
                )
                sent_anything = True

        if not sent_anything:
            raise ValidationError(_("After filtering, invoice has no lines/notes to send to PHC."))

        return move_content

    # -----------------------------------------------------------------
    #  CriaFTAD (downpayment) parameter builder
    # -----------------------------------------------------------------
    def _prepare_downpayment_parameter(self, move):
        """
        CriaFTAD expects:
          <doctype>   numeric(3,0)   -> 3
          <no>        numeric(10,0)
          <formpag>   varchar(25)    -> can be blank
          <descricao> varchar(50)
          <valor>     numeric(19,6)
          <tabiva>    numeric(1,0)
        """
        partner_ref = self._get_partner_phc_ref(move)
        if not partner_ref:
            raise ValidationError(_("Partner has no PHC number (ref). Sync client first."))

        no_value = self._digits_only(partner_ref, 10)
        if not no_value:
            raise ValidationError(_("Partner PHC reference must be numeric."))

        doctype_value = "1"
        formpag_value = ""

        dp_line = move.invoice_line_ids.filtered(lambda l: getattr(l, "is_downpayment", False))[:1]
        if dp_line and dp_line.name:
            descricao = dp_line.name
        else:
            descricao = move.name or move.partner_id.name or ""
        descricao_value = self._sanitize_text(descricao, 50)

        valor_value = self._sanitize_numeric(move.amount_total, precision=6, max_len=19)

        tabiva_value = "0"
        dp_line = move.invoice_line_ids.filtered(
            lambda l: getattr(l, "is_downpayment", False) and (l.quantity or 0.0) > 0 and (l.price_unit or 0.0) > 0
        )[:1]
        if dp_line and dp_line.tax_ids:
            tax = dp_line.tax_ids[0]
            if hasattr(tax, "x_studio_n_tabela_phc_1") and tax.x_studio_n_tabela_phc_1:
                tabiva_value = self._sanitize_text(str(int(tax.x_studio_n_tabela_phc_1)), 1)
            else:
                tabiva_value = self._sanitize_text(str(int(tax.amount or 0)), 1)

        return (
            f"<doctype>{doctype_value}</doctype>"
            f"<no>{no_value}</no>"
            f"<formpag>{formpag_value}</formpag>"
            f"<descricao>{descricao_value}</descricao>"
            f"<valor>{valor_value}</valor>"
            f"<tabiva>{tabiva_value}</tabiva>"
        )

    # -----------------------------------------------------------------
    #  CriaFTGT (delivery note / guia de transporte) parameter builder
    # -----------------------------------------------------------------
    def _prepare_delivery_parameter(self, picking):
        partner_ref = self._get_partner_phc_ref(picking)

        # Fallback: Odoo deliveries often carry a "Delivery Address" child contact
        # (type='delivery') as partner_id, which has no PHC ref of its own. In that
        # case fall back to the parent contact and treat it as the selected partner
        # for both identification (<no>) and address fields (<dmorada>, <dlocal>, ...).
        phc_partner = picking.partner_id
        if not partner_ref and picking.partner_id and picking.partner_id.parent_id:
            parent = picking.partner_id.parent_id.with_company(picking.company_id)
            if hasattr(parent, "_phc_get_effective_ref"):
                partner_ref = (parent._phc_get_effective_ref() or "").strip()
            else:
                partner_ref = (parent.ref or "").strip()
            if partner_ref:
                phc_partner = parent

        if not partner_ref:
            raise ValidationError(_("Partner has no PHC number (ref). Sync client first."))

        no_value = self._digits_only(partner_ref, 10)
        if not no_value:
            raise ValidationError(_("Partner PHC reference must be numeric."))

        load_dt = fields.Datetime.to_datetime(
            picking.date_done or picking.scheduled_date or fields.Datetime.now()
        )
        load_dt = fields.Datetime.context_timestamp(picking, load_dt)

        load_partner = False
        for chain in (
            "warehouse_address_id",
            "picking_type_id.warehouse_id.partner_id",
            "company_id.partner_id",
        ):
            candidate = self._get_chain_value(picking, chain)
            if candidate and hasattr(candidate, "_name") and candidate._name == "res.partner":
                load_partner = candidate
                break
        load_partner = load_partner or picking.company_id.partner_id
        discharge_partner = phc_partner.with_company(picking.company_id) if phc_partner else False
        discharge_partner = discharge_partner or load_partner
        discharge_address = ", ".join(
            value for value in [discharge_partner.street, discharge_partner.street2] if value
        )
        discharge_country = (
            getattr(discharge_partner, "x_studio_country_code", False)
            or (discharge_partner.country_id.code or "")
            or (discharge_partner.country_id.name or "")
        )
        discharge_zip = (discharge_partner.zip or "").strip()

        matricula_value = ""
        for chain in (
            "x_studio_matricula",
            "matricula",
            "sale_id.x_studio_matricula",
            "sale_id.matricula",
            "sale_id.carrier_id.x_studio_matricula",
            "sale_id.carrier_id.matricula",
            "sale_id.carrier_id.vehicle_id.license_plate",
        ):
            matricula_value = self._get_chain_value(picking, chain)
            if matricula_value:
                break
        if not matricula_value:
            raise ValidationError(_("Matricula is required to sync delivery documents to PHC."))

        move_content = (
            f"<doctype>11</doctype>"
            f"<no>{no_value}</no>"
            f"<matricula>{self._sanitize_text(matricula_value, 20)}</matricula>"
            f"<cdata>{load_dt.strftime('%Y-%m-%d')}</cdata>"
            f"<chora>{load_dt.strftime('%H:%M')}</chora>"
            f"<dmorada>{self._sanitize_text(discharge_address, 60)}</dmorada>"
            f"<dlocal>{self._sanitize_text(discharge_partner.city, 25)}</dlocal>"
            f"<dcodpost>{self._sanitize_text(discharge_zip, 15)}</dcodpost>"
            f"<pais>{self._sanitize_text(discharge_country, 20)}</pais>"
        )

        zero_qtd = self._sanitize_numeric(0.0, precision=3, max_len=12)
        lines = picking.move_ids_without_package.sorted(lambda move: (move.sequence, move.id))
        lines = lines.filtered(
            lambda move:
                move.state == "done"
                and move.product_id
                and not getattr(move, "scrapped", False)
                and move.quantity
        )
        if not lines:
            raise ValidationError(_("Delivery has no done lines to send to PHC."))

        sent_anything = False
        for line in lines:
            ref_src = (
                line.product_id.type
                or line.product_id.default_code
                or line.product_id.name
                or line.name
            )
            ref_mapped = self.PHC_REF_MAP.get((ref_src or "").strip().lower(), ref_src or "")
            ref_value = self._sanitize_text(ref_mapped, 18)
            if not ref_value:
                raise ValidationError(_("Each delivery line must have a PHC reference."))

            design_full = (
                line.description_picking
                or line.product_id.display_name
                or line.name
                or ""
            )
            design_parts = self._split_design_with_newlines(design_full, self.PHC_DESIGN_MAX)
            design_first = self._sanitize_text(design_parts[0], self.PHC_DESIGN_MAX)
            qtd_value = self._sanitize_numeric(line.quantity, precision=3, max_len=12)

            # Guias de Transporte are not tax documents, so <tabiva> must be
            # empty. Sending "0" makes PHC look up TAXASIVA code 0 and fail.
            move_content += (
                f"<ref>{ref_value}</ref>"
                f"<design>{design_first}</design>"
                f"<qtd>{qtd_value}</qtd>"
                f"<tabiva></tabiva>"
            )
            sent_anything = True

            for part in design_parts[1:]:
                part_value = self._sanitize_text(part, self.PHC_DESIGN_MAX)
                if not part_value:
                    continue
                move_content = self._append_blank_delivery_line(
                    move_content, part_value, zero_qtd
                )
                sent_anything = True

        if not sent_anything:
            raise ValidationError(_("After filtering, delivery has no lines to send to PHC."))

        return move_content

    # -----------------------------------------------------------------
    # Logging + sync
    # -----------------------------------------------------------------
    def create_logging_entry(self, env, db_name, move, message, parameter):
        env["ir.logging"].sudo().create({
            "name": "PHC: %s" % move.name,
            "type": "server",
            "dbname": db_name,
            "level": "DEBUG",
            "message": message,
            "path": "",
            "func": parameter,
            "line": ""
        })

    def _sync_invoice(self, db_name, move, payload, parameter):
        response = None
        message = None
        response_text = None
        fault_string = None

        move_name = getattr(move, "name", "?")
        payload_text = payload.decode("utf-8", errors="replace") if isinstance(payload, (bytes, bytearray)) else str(payload)
        _logger.info("PHC[%s] REQUEST URL: %s", move_name, self.url)
        _logger.info("PHC[%s] REQUEST PARAMETER:\n%s", move_name, parameter)
        _logger.info("PHC[%s] REQUEST PAYLOAD:\n%s", move_name, payload_text)

        try:
            resp = requests.post(
                url=self.url,
                headers=self.headers,
                data=payload,
                verify=self.verify_ssl,
            )

            response_text = resp.text
            _logger.info("PHC[%s] RESPONSE STATUS: %s", move_name, resp.status_code)
            _logger.info("PHC[%s] RESPONSE BODY:\n%s", move_name, response_text)
            if resp.status_code != 200:
                message = "Failure -> HTTP %s: %s" % (resp.status_code, response_text)
            else:
                xml_response = etree.fromstring(resp.content)
                namespaces = {
                    "soap": "http://schemas.xmlsoap.org/soap/envelope/",
                    "phc": "http://www.phc.pt/",
                }

                fault_el = xml_response.find(".//soap:Fault", namespaces=namespaces)
                if fault_el is not None:
                    fault_string_el = fault_el.find(".//faultstring")
                    if fault_string_el is not None:
                        fault_string = (fault_string_el.text or "").strip()

                run_code_result = xml_response.find(".//phc:RunCodeResult", namespaces=namespaces)
                parsed_result = (run_code_result.text or "").strip() if run_code_result is not None else None

                if parsed_result:
                    message = "Success -> " + parsed_result
                    try:
                        response = ast.literal_eval(parsed_result)
                    except Exception:
                        response = parsed_result
                    if not response:
                        message = "Failure -> Empty response"
                elif fault_string:
                    message = "Failure -> SOAP Fault: %s" % fault_string
                else:
                    message = "Failure -> No RunCodeResult returned"

        except Exception as e:
            message = "Failure -> " + str(e)
            response_text = response_text or str(e)
            _logger.exception("Error when syncing invoice to PHC: %s", e)

        self.create_logging_entry(
            env=move.env,
            db_name=db_name,
            move=move,
            message=message,
            parameter=parameter
        )

        response_text = response_text or message
        return response, response_text


# ============================================================
#  ODOO MODELS
# ============================================================

class AccountMove(models.Model):
    _inherit = "account.move"

    is_phc_synced = fields.Boolean(
        string="ERP Synced",
        default=False,
        help="True if invoice already synced to PHC."
    )
    phc_invoice = fields.Binary(
        string="ERP PDF",
        attachment=False,
        help="PDF returned by PHC."
    )
    filename = fields.Char(
        string="Ficheiro",
        help="PDF name returned by PHC."
    )
    x_studio_logs_downpayment = fields.Text(
        string="Downpayment Logs",
        help="Internal notes/debug for downpayment logic."
    )
    phc_last_response = fields.Text(
        string="PHC Last Response",
        help="Raw PHC SOAP response."
    )

    # Stored on DOWNPAYMENT invoices after CriaFTAD returns them
    x_studio_phc_ad_ano = fields.Char(
        string="PHC Ano (Adiantamento)",
        size=4,
        readonly=True
    )
    x_studio_phc_ad_num = fields.Char(
        string="PHC FT_Adiantamento",
        size=10,
        readonly=True
    )

    x_studio_doctype_phc = fields.Integer(
        string="PHC Doctype",
        default=1,
        help="PHC document type. Used in <doctype>."
    )

    is_downpayment = fields.Boolean(
        string="Is Downpayment",
        compute="_compute_is_downpayment",
        store=True,
        readonly=True,
        help="True if any line is is_downpayment=True and has positive qty/price."
    )

    @api.depends(
        "invoice_line_ids.is_downpayment",
        "invoice_line_ids.quantity",
        "invoice_line_ids.price_unit",
        "invoice_line_ids.display_type",
    )
    def _compute_is_downpayment(self):
        for move in self:
            down = False
            for line in move.invoice_line_ids:
                if line.display_type in ("line_section", "line_note"):
                    continue
                is_dp = bool(getattr(line, "is_downpayment", False))
                qty = line.quantity or 0.0
                pu = line.price_unit or 0.0
                if is_dp and qty > 0 and pu > 0:
                    down = True
                    break

            move.is_downpayment = down

            wanted_doctype = 1 if down else 1
            if move.x_studio_doctype_phc != wanted_doctype:
                move.x_studio_doctype_phc = wanted_doctype

    # ---------------------------------------------------------
    # Downpayment refs collection for FINAL invoice
    # ---------------------------------------------------------
    def _phc_collect_downpayment_refs(self):
        """
        For final invoices:
        - find negative downpayment lines
        - parse "INV/...." from their description
        - load that invoice and read x_studio_phc_ad_ano + x_studio_phc_ad_num
        Returns: list of dicts: [{"ano": "2025", "num": "11"}, ...] (max 10)
        """
        self.ensure_one()

        refs = []
        neg_dp_lines = self.invoice_line_ids.filtered(
            lambda l: getattr(l, "is_downpayment", False) and (l.quantity or 0.0) < 0
        )

        inv_regex = re.compile(r"\b([A-Z]{2,5}/\d{4}/\d+)\b")

        for line in neg_dp_lines:
            name = line.name or ""
            m = inv_regex.search(name)
            if not m:
                continue

            inv_name = m.group(1)
            dp_move = self.env["account.move"].search(
                [("name", "=", inv_name), ("move_type", "=", self.move_type)],
                limit=1
            )
            if not dp_move:
                continue

            ano = (dp_move.x_studio_phc_ad_ano or "").strip()
            num = (dp_move.x_studio_phc_ad_num or "").strip()
            if ano and num:
                refs.append({"ano": ano, "num": num})

            if len(refs) >= 10:
                break

        return refs

    # ---------------------------------------------------------
    # Helpers to connect and sync
    # ---------------------------------------------------------
    def pre_validation(self, company):
        err_msg = ''
        base_url = (company.phc_api_base_url or '').strip()
        username = (company.phc_api_user or '').strip()
        password = (company.phc_api_password or '').strip()

        if not base_url:
            err_msg += '\n PHC WS URL'
        if not username:
            err_msg += '\n Utilizador PHC'
        if not password:
            err_msg += '\n Password PHC'
        if err_msg:
            err_msg = 'Please configure below fields in company settings: ' + err_msg
            raise ValidationError(_(err_msg))

        return base_url, username, password

    def _get_phc_connection(self):
        self.ensure_one()
        base_url, username, password = self.pre_validation(self.company_id)
        return PHCConnection(
            url=base_url,
            username=username,
            password=password,
            verify_ssl=False,
        )

    def connect_phc_and_sync_invoice(self):
        self.ensure_one()
        if not self.is_sale_document(include_receipts=True):
            return

        conn = self._get_phc_connection()

        force = bool(self.env.context.get("phc_force_resync"))

        if self.is_phc_synced and not force:
            return

        if self.is_downpayment and (self.x_studio_phc_ad_ano or self.x_studio_phc_ad_num) and not force:
            return

        phc_code = "CriaFTAD" if self.is_downpayment else "CriaFT"

        ctx = dict(self.env.context)
        if phc_code == "CriaFT":
            dp_refs = self._phc_collect_downpayment_refs()
            if dp_refs:
                ctx["phc_dp_refs"] = dp_refs

        move_ctx = self.with_context(**ctx)

        payload, parameter = conn._set_template_details(
            move=move_ctx,
            phc_code=phc_code,
            xml_filename="send_invoice.xml",
        )

        response, response_text = conn._sync_invoice(
            db_name=self._cr.dbname, move=move_ctx, payload=payload, parameter=parameter
        )

        invoice_payload = None
        if isinstance(response, list) and response:
            invoice_payload = response[0]
        elif isinstance(response, dict):
            invoice_payload = response

        if phc_code == "CriaFTAD" and isinstance(invoice_payload, dict):
            ano = (invoice_payload.get("Ano") or "").strip()
            num = (invoice_payload.get("FT_Adiantamento") or "").strip()
            if ano and num:
                self.sudo().write({
                    "x_studio_phc_ad_ano": re.sub(r"\D", "", ano)[:4],
                    "x_studio_phc_ad_num": re.sub(r"\D", "", num)[:10],
                })

        if invoice_payload and invoice_payload.get("PDF"):
            self.is_phc_synced = True
            pdf_url = invoice_payload.get("PDF")
            pdf_name = pdf_url.rsplit("/", 1)[1]
            self.add_phc_pdf_to_attachment(pdf_url, pdf_name)
        else:
            self.is_phc_synced = False

        self.phc_last_response = (
            f"[PHC CODE={phc_code}]\n"
            f"[PARAMETER]\n{parameter}\n\n"
            f"[RESPONSE]\n{response_text or ''}"
        )

    def action_sync_to_phc(self):
        self.ensure_one()
        self.connect_phc_and_sync_invoice()

    def _post(self, soft=True):
        moves = super(AccountMove, self)._post(soft)
        for move in moves.filtered(lambda m: m.is_sale_document(include_receipts=True) and not m.is_phc_synced):
            move.connect_phc_and_sync_invoice()
        return moves

    def add_phc_pdf_to_attachment(self, pdf_url, pdf_name):
        import base64
        self.ensure_one()
        content = base64.encodebytes(requests.get(pdf_url, verify=False).content)
        attachment = self.env["ir.attachment"].create({
            "name": pdf_name,
            "datas": content,
            "store_fname": pdf_name,
            "res_model": self._name,
            "res_id": self.id,
            "res_name": self.name,
            "type": "binary",
            "mimetype": "application/pdf",
        })

        self.message_post(
            body="PHC PDF added in attachment.",
            attachment_ids=attachment.ids
        )
        self.write({"phc_invoice": content, "filename": pdf_name})


class AccountJournal(models.Model):
    _inherit = "account.journal"

    x_studio_doctype_phc = fields.Integer(
        string="PHC Doctype (Journal Default)",
        help="Default PHC doctype for invoices of this journal."
    )


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # x_studio_tipo_de_artigo related to product.type (consu/service/combo)
    x_studio_tipo_de_artigo = fields.Selection(
        related="product_id.type",
        store=True,
        readonly=True,
        string="Tipo de Artigo (PHC)",
        help="Related to product.type (consu/service/combo). Used in PHC <ref>."
    )


class AccountTax(models.Model):
    _inherit = "account.tax"

    x_studio_n_tabela_phc_1 = fields.Integer(
        string="Nº Tabela IVA PHC",
        help="PHC tax table number (numeric(1,0)). Used in <tabiva>."
    )
