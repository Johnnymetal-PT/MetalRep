"""Sincronizacao de account.payment entre PICCOLO e PICCOLO_COMMUNITY.

O ``ref`` do pagamento e o input principal: tem de conter os nomes
das faturas a liquidar separados por virgula, ponto-e-virgula ou
nova linha. Exemplo:
    "INV/2026/0058, INV/2026/0059"

O sync cria UM pagamento agregado na BD destino via
``account.payment.register`` ligado a todas as faturas referenciadas.

Valores HARDCODED:
- ``second_db = "PICCOLO_COMMUNITY"``
- ``fixed_journal_id = 14`` (journal de pagamentos no destino)
- Campo ``x_studio_observaes_no_recibo`` (typo intencional herdado).
"""
import logging
import re

import odoo
from odoo import _, api, models

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @staticmethod
    def _split_invoice_refs(ref_text):
        """Parse de ``ref`` em lista de nomes de fatura.

        Aceita separadores ``,``, ``;`` e ``\\n``. Preserva ordem do
        utilizador removendo duplicados (dict.fromkeys preserva ordem
        em Python 3.7+).
        """
        if not ref_text:
            return []
        raw_parts = re.split(r"[,;\n]+", ref_text)
        cleaned = [part.strip() for part in raw_parts if part and part.strip()]
        return list(dict.fromkeys(cleaned))

    @staticmethod
    def _ensure_manual_char_field(env, model_name, field_name, field_description):
        """Cria um Char field 'manual' (ir.model.fields) se nao existir.

        Usado para garantir que o campo Studio
        ``x_studio_observaes_no_recibo`` existe na BD destino antes
        de tentar escrever nele.
        """
        field_model = env["ir.model.fields"].sudo()
        existing = field_model.search(
            [("model", "=", model_name), ("name", "=", field_name)], limit=1
        )
        if existing:
            return existing

        model = env["ir.model"].sudo().search([("model", "=", model_name)], limit=1)
        if not model:
            raise ValueError(_("Model not found in second database: %s") % model_name)

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
        """Replica este pagamento para PICCOLO_COMMUNITY.

        Procura as faturas referenciadas em ``self.ref`` na BD destino
        e cria um unico ``account.payment`` agregado via
        ``account.payment.register``.
        """
        self.ensure_one()
        _logger.info("Starting payment synchronization for payment ID: %s", self.id)

        second_db = "PICCOLO_COMMUNITY"
        fixed_journal_id = 14  # HARDCODED - journal de pagamento na destino
        source_receipt_note_field = "x_studio_observaes_no_recibo"  # typo intencional

        try:
            registry = odoo.registry(second_db)
            if not registry:
                raise ValueError(_("Registry for database %s not found") % second_db)

            with registry.cursor() as cr:
                second_env = api.Environment(cr, self.env.uid, {})

                # Forcar acesso multi-company (igual logica do account_move.py)
                companies = second_env["res.company"].sudo().search([]).ids
                if not companies:
                    raise ValueError(_("No companies found in database %s") % second_db)

                second_env = api.Environment(
                    cr,
                    self.env.uid,
                    {"allowed_company_ids": companies, "force_company": companies[0]},
                )

                # Cliente: matching por nome; cria se nao existir.
                customer = second_env["res.partner"].sudo().search(
                    [("name", "=", self.partner_id.name)], limit=1
                )
                if not customer:
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

                # ---- Faturas referenciadas ----
                invoice_names = self._split_invoice_refs(self.ref)
                if not invoice_names:
                    raise ValueError(_("No invoice references found in payment memo (ref)."))

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

                # Primeiro tenta com filtro de partner; se faltarem
                # faturas, refaz sem filtro de partner (mais permissivo).
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

                # Preserva ordem do utilizador no recordset.
                invoice_map = {inv.name: inv for inv in invoices}
                ordered_invoices = invoice_model.browse(
                    [invoice_map[name].id for name in invoice_names]
                )

                # Valida que as faturas pertencem ao mesmo cliente
                # na BD destino (o matching por nome pode atravessar
                # partners distintos em caso de duplicados).
                partners = ordered_invoices.mapped("partner_id")
                if len(partners) > 1:
                    raise ValueError(
                        _("Matched invoices belong to different customers in second database.")
                    )
                target_partner = partners[:1] if partners else customer

                # Payment method: tenta match por nome; fallback ao
                # primeiro disponivel (mantem o sync a funcionar mesmo
                # com nomenclaturas divergentes).
                payment_method_name = (
                    self.payment_method_line_id.name if self.payment_method_line_id else None
                )
                payment_method_line = None
                if payment_method_name:
                    payment_method_line = (
                        second_env["account.payment.method.line"].sudo()
                        .search([("name", "=", payment_method_name)], limit=1)
                    )
                if not payment_method_line:
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
                    # group_payment=True quando ha mais que 1 fatura -
                    # cria UM pagamento agregado ligado a todas.
                    "group_payment": len(ordered_invoices) > 1,
                }

                # Observacoes no recibo (campo Studio com typo)
                receipt_note = False
                if source_receipt_note_field in self._fields:
                    receipt_note = self[source_receipt_note_field]

                payment_model = second_env["account.payment"].sudo()
                # Garante o campo Studio na BD destino se nao existir.
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
                    # Refrescar o model apos criar o campo.
                    payment_model = second_env["account.payment"].sudo()

                # Usa o wizard account.payment.register para criar e
                # ligar o pagamento as faturas (sem ter de fazer
                # reconciliation manual).
                payment_wizard = second_env["account.payment.register"].with_context(
                    active_model="account.move",
                    active_ids=ordered_invoices.ids,
                ).create(payment_vals)

                created_payments = second_env["account.payment"]
                # _create_payments existe em versoes mais recentes;
                # action_create_payments e o fallback (so retorna act).
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

                # Flag de sincronizado - dois nomes possiveis na origem
                # consoante o versionamento Studio.
                sync_flag = {}
                if "x_studio_community_1" in self._fields:
                    sync_flag["x_studio_community_1"] = True
                elif "x_studio_community" in self._fields:
                    sync_flag["x_studio_community"] = True
                if sync_flag:
                    self.sudo().write(sync_flag)

                self.message_post(body=_("Payment successfully synced."))
                return True

        except Exception as e:
            _logger.error("Failed to sync payment: %s", str(e))
            raise ValueError(_("Failed to sync payment: %s") % str(e))

    def mark_as_sent(self):
        """Reconcilia pagamentos manuais posted com faturas em ``ref``.

        Utilitario para casos em que o pagamento foi criado/posted
        manualmente mas a reconciliacao com a fatura nao aconteceu.
        So opera quando: state=posted, ainda nao marcado como sent,
        e payment_method_code='manual'.
        """
        for payment in self:
            if payment.state != "posted":
                continue
            if payment.is_move_sent:
                continue
            if payment.payment_method_code != "manual":
                continue

            invoice_refs = self._split_invoice_refs(payment.ref)
            if not invoice_refs:
                continue

            invoices = self.env["account.move"].search(
                [
                    ("name", "in", invoice_refs),
                    ("state", "=", "posted"),
                    ("move_type", "in", ["out_invoice", "in_invoice"]),
                ]
            )
            if not invoices:
                continue

            # Linhas reconciliaveis (account.reconcile=True) e ainda
            # nao reconciliadas.
            payment_move_lines = payment.move_id.line_ids.filtered(
                lambda line: line.account_id.reconcile and not line.reconciled
            )
            invoice_move_lines = invoices.line_ids.filtered(
                lambda line: line.account_id.reconcile and not line.reconciled
            )

            if not invoice_move_lines:
                # Fatura ja reconciliada por outra via - marca como paga
                # manualmente para nao deixar pendente.
                for invoice in invoices:
                    invoice.payment_state = "paid"
            elif payment_move_lines:
                try:
                    (invoice_move_lines + payment_move_lines).reconcile()
                except Exception as exc:
                    _logger.error(
                        "Reconciliation failed for payment %s: %s",
                        payment.name, str(exc),
                    )

            payment.is_move_sent = True
