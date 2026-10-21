import logging
import re
import odoo

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _split_ref_to_invoice_names(self, ref):
        """Fallback: parse ref into a list of names."""
        if not ref:
            return []
        return [
            part.strip()
            for part in re.split(r"[;,]", ref)
            if part.strip()
        ]

    def action_sync_payment(self):
        """
        Sync payment with another Odoo database.

        - Uses ALL invoices linked to the payment (reconciled_invoice_ids).
        - Finds matching invoices in the Community DB by name.
        - Registers ONE grouped payment there against all those invoices.
        - Explicitly sets the payment.ref in Community DB to all invoice names.
        """
        self.ensure_one()

        _logger.info("🧩 Starting payment synchronization for Payment ID: %s", self.id)

        second_db = "PICCOLO_COMMUNITY"
        fixed_journal_id = 14  # Always apply Journal ID 14 in second database

        try:
            registry = odoo.registry(second_db)
            if not registry:
                raise ValueError(f"❌ Registry for database {second_db} not found!")

            with registry.cursor() as cr:
                second_env = api.Environment(cr, self.env.uid, {})

                # --- Companies in second DB ---
                companies = second_env["res.company"].sudo().search([]).ids
                if not companies:
                    raise ValueError("❌ No companies found in second database!")

                second_env = api.Environment(cr, self.env.uid, {
                    "allowed_company_ids": companies,
                    "force_company": companies[0],
                })

                _logger.info("✅ Successfully switched to database: %s", second_db)

                # -----------------------------------------------------------------
                # 1. Ensure Customer Exists
                # -----------------------------------------------------------------
                customer = second_env["res.partner"].sudo().search(
                    [("name", "=", self.partner_id.name)], limit=1
                )

                if not customer:
                    _logger.info("🧩 Customer not found. Creating new customer: %s", self.partner_id.name)
                    customer = second_env["res.partner"].sudo().create({
                        "name": self.partner_id.name,
                        "email": self.partner_id.email,
                        "phone": self.partner_id.phone,
                        "street": self.partner_id.street,
                        "city": self.partner_id.city,
                        "zip": self.partner_id.zip,
                        "country_id": self.partner_id.country_id.id if self.partner_id.country_id else False,
                        "vat": self.partner_id.vat,
                        "customer_rank": 1,
                    })
                    _logger.info("✅ New customer created: ID %s", customer.id)

                # -----------------------------------------------------------------
                # 2. Collect all invoice names to sync
                # -----------------------------------------------------------------
                # Preferred source: reconciled invoices in the ORIGINAL DB
                invoice_names = self.reconciled_invoice_ids.mapped("name")

                # Fallback: parse ref if no reconciled invoices available
                if not invoice_names and self.ref:
                    invoice_names = self._split_ref_to_invoice_names(self.ref)

                if not invoice_names:
                    raise ValueError(
                        f"❌ No invoice names found in payment (reconciled_invoice_ids or ref). "
                        f"Payment: {self.name}"
                    )

                _logger.info("🔍 Looking for invoices in second DB with names: %s", invoice_names)

                invoices = second_env["account.move"].sudo().search([
                    ("name", "in", invoice_names),
                    ("move_type", "in", ["out_invoice", "in_invoice"]),
                    ("state", "=", "posted"),
                    ("partner_id", "=", customer.id),
                ])

                if not invoices:
                    raise ValueError(
                        f"❌ No matching invoices found in second database for names: {invoice_names}"
                    )

                _logger.info("✅ Found %s invoice(s) in second DB: %s",
                             len(invoices), invoices.mapped("name"))

                # Build a clean ref/communication string for the Community payment
                ref_string = ", ".join(invoices.mapped("name"))

                # -----------------------------------------------------------------
                # 3. Match Payment Method
                # -----------------------------------------------------------------
                payment_method_name = (
                    self.payment_method_line_id.name
                    if self.payment_method_line_id
                    else None
                )
                payment_method_line = None

                if payment_method_name:
                    _logger.info(
                        "🔍 Searching for Payment Method in second database: %s",
                        payment_method_name,
                    )
                    payment_method_line = second_env["account.payment.method.line"].sudo().search(
                        [("name", "=", payment_method_name)],
                        limit=1,
                    )

                if not payment_method_line:
                    _logger.warning(
                        "⚠ Payment method not found in second database. Using default method."
                    )
                    payment_method_line = (
                        second_env["account.payment.method.line"].sudo().search([], limit=1)
                    )

                if not payment_method_line:
                    raise ValueError("❌ No available payment method found in second database!")

                # -----------------------------------------------------------------
                # 4. Register ONE grouped Payment via `account.payment.register`
                # -----------------------------------------------------------------
                payment_vals = {
                    "amount": self.amount,           # grouped amount as in original DB
                    "payment_date": self.date,
                    "journal_id": fixed_journal_id,
                    "payment_method_line_id": payment_method_line.id,
                    "payment_type": self.payment_type,
                    "partner_type": self.partner_type,
                    "partner_id": customer.id,
                    "currency_id": self.currency_id.id,
                    "communication": ref_string,    # label / memo
                    "group_payment": True,          # 💥 force SINGLE grouped payment
                }

                _logger.info(
                    "✅ Registering grouped payment for invoices: %s with ref '%s'",
                    invoices.mapped("name"),
                    ref_string,
                )

                payment_wizard = second_env["account.payment.register"].with_context(
                    active_model="account.move",
                    active_ids=invoices.ids,        # all invoices in one go
                ).create(payment_vals)

                # Create the payment(s); with group_payment=True this should be ONE
                payments = payment_wizard._create_payments()
                _logger.info("✅ Created payments in second DB (should be 1): %s", payments.ids)

                # Safety: if Odoo still created more than one (e.g. different partners),
                # we at least update all of them.
                if payments:
                    payments.sudo().write({"ref": ref_string})

                # -----------------------------------------------------------------
                # 5. Mark as Synced
                # -----------------------------------------------------------------
                self.sudo().write({"x_studio_community_1": True})
                _logger.info("✅ Payment marked as synced (x_studio_community_1 = True)")

                self.message_post(body=_("✅ Payment successfully synced."))
                return True

        except Exception as e:
            _logger.error("❌ Failed to register payment in second database: %s", str(e))
            raise ValueError(_("Failed to sync payment: %s") % str(e))

