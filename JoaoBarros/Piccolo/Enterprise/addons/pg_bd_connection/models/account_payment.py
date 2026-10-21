import logging
import re

import odoo
from odoo import _, api, models

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @staticmethod
    def _split_invoice_refs(ref_text):
        if not ref_text:
            return []
        raw_parts = re.split(r"[,;\n]+", ref_text)
        cleaned = [part.strip() for part in raw_parts if part and part.strip()]
        # Preserve user order while removing duplicates.
        return list(dict.fromkeys(cleaned))

    @staticmethod
    def _ensure_manual_char_field(env, model_name, field_name, field_description):
        field_model = env["ir.model.fields"].sudo()
        existing = field_model.search(
            [("model", "=", model_name), ("name", "=", field_name)], limit=1
        )
        if existing:
            return existing

        model = env["ir.model"].sudo().search([("model", "=", model_name)], limit=1)
        if not model:
            raise ValueError(_("Model not found in second database: %s") % model_name)

        _logger.info(
            "Creating missing field %s on model %s in second database",
            field_name,
            model_name,
        )
        return field_model.create(
            {
                "name": field_name,
                "field_description": field_description,
                "model_id": model.id,
                "model": model_name,
                "ttype": "char",
                "state": "manual",
            }
        )

    def action_sync_payment(self):
        """
        Sync payment with another Odoo database by matching invoice names in `ref`
        and creating one payment registration for all matched invoices.
        """
        self.ensure_one()
        _logger.info("Starting payment synchronization for payment ID: %s", self.id)

        second_db = "PICCOLO_COMMUNITY"
        fixed_journal_id = 14
        source_receipt_note_field = "x_studio_observaes_no_recibo"

        try:
            registry = odoo.registry(second_db)
            if not registry:
                raise ValueError(_("Registry for database %s not found") % second_db)

            with registry.cursor() as cr:
                second_env = api.Environment(cr, self.env.uid, {})

                companies = second_env["res.company"].sudo().search([]).ids
                if not companies:
                    raise ValueError(_("No companies found in database %s") % second_db)

                second_env = api.Environment(
                    cr,
                    self.env.uid,
                    {"allowed_company_ids": companies, "force_company": companies[0]},
                )
                _logger.info("Switched to database %s", second_db)

                customer = second_env["res.partner"].sudo().search(
                    [("name", "=", self.partner_id.name)], limit=1
                )
                if not customer:
                    _logger.info(
                        "Customer not found. Creating customer: %s",
                        self.partner_id.name,
                    )
                    customer = second_env["res.partner"].sudo().create(
                        {
                            "name": self.partner_id.name,
                            "email": self.partner_id.email,
                            "phone": self.partner_id.phone,
                            "street": self.partner_id.street,
                            "city": self.partner_id.city,
                            "zip": self.partner_id.zip,
                            "country_id": (
                                self.partner_id.country_id.id
                                if self.partner_id.country_id
                                else False
                            ),
                            "vat": self.partner_id.vat,
                            "customer_rank": 1,
                        }
                    )

                invoice_names = self._split_invoice_refs(self.ref)
                if not invoice_names:
                    raise ValueError(
                        _("No invoice references found in payment memo (ref).")
                    )

                invoice_model = second_env["account.move"].sudo()
                invoice_domain = [
                    ("name", "in", invoice_names),
                    ("state", "=", "posted"),
                    (
                        "move_type",
                        "in",
                        ["out_invoice", "in_invoice", "out_refund", "in_refund"],
                    ),
                ]

                invoices = invoice_model.search(
                    invoice_domain + [("partner_id", "=", customer.id)]
                )
                if len(invoices) < len(invoice_names):
                    invoices = invoice_model.search(invoice_domain)

                found_names = set(invoices.mapped("name"))
                missing_names = [name for name in invoice_names if name not in found_names]
                if missing_names:
                    raise ValueError(
                        _("No matching invoice found in second database for: %s")
                        % ", ".join(missing_names)
                    )

                invoice_map = {inv.name: inv for inv in invoices}
                ordered_invoices = invoice_model.browse(
                    [invoice_map[name].id for name in invoice_names]
                )

                partners = ordered_invoices.mapped("partner_id")
                if len(partners) > 1:
                    raise ValueError(
                        _(
                            "Matched invoices belong to different customers in second database."
                        )
                    )
                target_partner = partners[:1] if partners else customer

                payment_method_name = (
                    self.payment_method_line_id.name if self.payment_method_line_id else None
                )
                payment_method_line = None
                if payment_method_name:
                    payment_method_line = (
                        second_env["account.payment.method.line"]
                        .sudo()
                        .search([("name", "=", payment_method_name)], limit=1)
                    )
                if not payment_method_line:
                    _logger.warning(
                        "Payment method %s not found in second DB. Using first available method.",
                        payment_method_name,
                    )
                    payment_method_line = (
                        second_env["account.payment.method.line"].sudo().search([], limit=1)
                    )
                if not payment_method_line:
                    raise ValueError(_("No payment method found in second database"))

                payment_vals = {
                    "amount": self.amount,
                    "payment_date": self.date,
                    "journal_id": fixed_journal_id,
                    "payment_method_line_id": payment_method_line.id,
                    "payment_type": self.payment_type,
                    "partner_type": self.partner_type,
                    "partner_id": target_partner.id,
                    "currency_id": self.currency_id.id,
                    "communication": self.ref,
                    "group_payment": len(ordered_invoices) > 1,
                }

                receipt_note = False
                if source_receipt_note_field in self._fields:
                    receipt_note = self[source_receipt_note_field]

                payment_model = second_env["account.payment"].sudo()
                if (
                    source_receipt_note_field not in payment_model._fields
                    and source_receipt_note_field in self._fields
                ):
                    self._ensure_manual_char_field(
                        second_env,
                        "account.payment",
                        source_receipt_note_field,
                        "Observacoes No Recibo",
                    )
                    payment_model = second_env["account.payment"].sudo()

                payment_wizard = second_env["account.payment.register"].with_context(
                    active_model="account.move",
                    active_ids=ordered_invoices.ids,
                ).create(payment_vals)

                created_payments = second_env["account.payment"]
                if hasattr(payment_wizard, "_create_payments"):
                    created_payments = payment_wizard._create_payments()
                else:
                    payment_wizard.action_create_payments()
                    created_payments = payment_model.search(
                        [
                            ("partner_id", "=", target_partner.id),
                            ("amount", "=", self.amount),
                            ("date", "=", self.date),
                        ],
                        order="id desc",
                        limit=1,
                    )

                if (
                    receipt_note
                    and source_receipt_note_field in payment_model._fields
                    and created_payments
                ):
                    created_payments.sudo().write({source_receipt_note_field: receipt_note})

                sync_flag = {}
                if "x_studio_community_1" in self._fields:
                    sync_flag["x_studio_community_1"] = True
                elif "x_studio_community" in self._fields:
                    sync_flag["x_studio_community"] = True
                if sync_flag:
                    self.sudo().write(sync_flag)

                self.message_post(body=_("Payment successfully synced."))
                _logger.info(
                    "Payment synced successfully. Payment ID: %s, invoices: %s",
                    self.id,
                    ", ".join(invoice_names),
                )
                return True

        except Exception as e:
            _logger.error("Failed to sync payment: %s", str(e))
            raise ValueError(_("Failed to sync payment: %s") % str(e))

    def mark_as_sent(self):
        """Mark manual posted payments as sent and reconcile with referenced invoices."""
        for payment in self:
            _logger.info("Processing payment %s (state=%s)", payment.name, payment.state)

            if payment.state != "posted":
                _logger.warning("Skipping %s: payment is not posted.", payment.name)
                continue
            if payment.is_move_sent:
                _logger.warning("Skipping %s: payment already marked as sent.", payment.name)
                continue
            if payment.payment_method_code != "manual":
                _logger.warning("Skipping %s: payment method is not manual.", payment.name)
                continue

            invoice_refs = self._split_invoice_refs(payment.ref)
            if not invoice_refs:
                _logger.warning(
                    "Skipping %s: no invoice reference found in payment memo.",
                    payment.name,
                )
                continue

            invoices = self.env["account.move"].search(
                [
                    ("name", "in", invoice_refs),
                    ("state", "=", "posted"),
                    ("move_type", "in", ["out_invoice", "in_invoice"]),
                ]
            )
            if not invoices:
                _logger.warning(
                    "Payment %s: no matching invoice found for ref '%s'.",
                    payment.name,
                    payment.ref,
                )
                continue

            payment_move_lines = payment.move_id.line_ids.filtered(
                lambda line: line.account_id.reconcile and not line.reconciled
            )
            invoice_move_lines = invoices.line_ids.filtered(
                lambda line: line.account_id.reconcile and not line.reconciled
            )

            if not invoice_move_lines:
                for invoice in invoices:
                    _logger.warning(
                        "No valid invoice move lines for invoice %s. Marking as paid manually.",
                        invoice.name,
                    )
                    invoice.payment_state = "paid"
            elif payment_move_lines:
                try:
                    (invoice_move_lines + payment_move_lines).reconcile()
                    _logger.info(
                        "Reconciliation successful for payment %s and invoices %s.",
                        payment.name,
                        ", ".join(invoices.mapped("name")),
                    )
                except Exception as exc:
                    _logger.error(
                        "Reconciliation failed for payment %s: %s",
                        payment.name,
                        str(exc),
                    )

            payment.is_move_sent = True
            _logger.info("Payment %s marked as sent.", payment.name)
