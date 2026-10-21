"""Sincronizacao de account.move entre PICCOLO e PICCOLO_COMMUNITY.

Replica uma fatura da BD origem para a BD destino chamando
``odoo.registry(second_db)`` diretamente (sem XML-RPC).

Fluxo em resumo:
1. Na BD origem: muda journal_id para 50 e posta a fatura se estiver draft.
2. Na BD destino: garante coluna ``account_move.delivery_count``,
   procura/cria partner por nome, resolve/cria a morada de entrega
   (``partner_shipping_id``) como contacto ``type=delivery`` filho do
   cliente, replica linhas, cria fatura em draft.
3. Marca a fatura origem com ``x_studio_community=True``.

Valores HARDCODED relevantes:
- ``first_db = "PICCOLO"``
- ``second_db = "PICCOLO_COMMUNITY"``
- ``journal_id = 50`` (BD origem, apos sync)
"""
import logging
import odoo
from psycopg2 import sql
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


def _ensure_column(env, table, column, column_def):
    """Garante que ``column`` existe em ``table`` (DDL fora do ORM).

    Usado para criar ``account_move.delivery_count`` na BD destino
    quando a coluna ainda nao foi propagada pelo modulo respetivo.
    Faz commit imediato porque ALTER TABLE precisa de existir antes
    do INSERT seguinte.
    """
    env.cr.execute(
        """SELECT 1 FROM information_schema.columns
            WHERE table_name=%s AND column_name=%s""",
        (table, column),
    )
    if not env.cr.fetchone():
        _logger.warning("Column %s.%s missing. Creating it.", table, column)
        env.cr.execute(
            sql.SQL("ALTER TABLE {} ADD COLUMN {} {}")
            .format(sql.Identifier(table), sql.Identifier(column), sql.SQL(column_def))
        )
        env.cr.commit()


class AccountMove(models.Model):
    _inherit = "account.move"

    # Permite manter o link a fatura original em PICCOLO depois do sync.
    x_original_invoice_id = fields.Integer(string="Original Invoice ID", copy=False)

    def action_sync_invoice(self):
        """Confirma a fatura na BD origem e replica-a para a BD destino."""
        _logger.info("Starting invoice synchronization for Invoice ID: %s", self.id)

        # Nomes HARDCODED - alinhados com as BDs Piccolo/Community.
        first_db = "PICCOLO"
        second_db = "PICCOLO_COMMUNITY"

        # ---- 1) BD origem: forcar journal=50 e posting da fatura ----
        try:
            registry = odoo.registry(first_db)
            if not registry:
                raise ValueError(f"Registry for database {first_db} not found!")

            with registry.cursor() as cr:
                first_env = api.Environment(cr, self.env.uid, {})

                # Le a propria fatura via cursor proprio para escrever com commit
                # explicito (assegurar persistencia antes da segunda BD).
                original_invoice = first_env["account.move"].sudo().search([("id", "=", self.id)], limit=1)

                if not original_invoice:
                    raise ValueError(f"No matching invoice found in first database for ID {self.id}")

                # Journal 50 e o destino correto antes de postar (regra de
                # negocio). So e aplicavel enquanto a move esta draft: moves
                # ja posted (ex.: notas de credito emitidas/certificadas) nao
                # permitem trocar de journal, pelo que se salta a escrita.
                if original_invoice.state != "posted":
                    original_invoice.sudo().write({"journal_id": 50})
                    cr.commit()

                    # Posta agora para que a move origem esteja
                    # contabilisticamente fechada no momento do sync.
                    original_invoice.sudo().action_post()
                    cr.commit()

        except Exception as e:
            _logger.error("Failed to confirm invoice in first database: %s", str(e))
            raise ValueError(_("Could not confirm invoice in first database: %s") % str(e))

        # ---- 2) BD destino: replicar a fatura ----
        try:
            registry = odoo.registry(second_db)
            if not registry:
                raise ValueError(f"Registry for database {second_db} not found!")

            with registry.cursor() as cr:
                second_env = api.Environment(cr, self.env.uid, {})

                # Forcar acesso a todas as companhias para que a fatura possa
                # ser criada sem barreiras de multi-company.
                companies = second_env["res.company"].sudo().search([]).ids
                if not companies:
                    raise ValueError(f"No companies found in database {second_db}")

                second_env = api.Environment(cr, self.env.uid, {
                    "allowed_company_ids": companies,
                    "force_company": companies[0],
                })

                second_env.user_id = second_env["res.users"].browse(self.env.uid).sudo()
                second_env.user_id.sudo().write({
                    "company_ids": [(6, 0, companies)],
                    "company_id": companies[0],
                })

                # Coluna delivery_count e referenciada pela vista replicada;
                # garante existencia mesmo que o modulo respetivo nao a tenha
                # criado na destino.
                _ensure_column(second_env, "account_move", "delivery_count", "INTEGER DEFAULT 0")

                # ---- Partner: matching por nome (case-sensitive) ----
                customer = second_env["res.partner"].sudo().search([("name", "=", self.partner_id.name)], limit=1)

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

                # ---- Journal de venda no destino ----
                journal = second_env["account.journal"].sudo().search([("type", "=", "sale")], limit=1)
                if not journal:
                    raise ValueError("No sales journal found in second database!")

                if not journal.default_account_id:
                    raise ValueError(f"Journal {journal.name} does not have a default account assigned!")

                account_id = journal.default_account_id.id

                # ---- Notas de credito: replicar via reversao standard ----
                # Uma NC nao pode ser criada como move "solto" no destino: a
                # certificacao fiscal PT exige que cada linha esteja ligada a
                # fatura original ("...is not related to the original invoice").
                # Por isso reproduz-se aqui a reversao standard sobre a fatura
                # original ja sincronizada, o que preenche nativamente
                # reversed_entry_id (e origin_line_id via account_invoice_refund_link).
                is_refund = self.move_type in ("out_refund", "in_refund")
                if is_refund:
                    if not self.reversed_entry_id:
                        raise ValueError(_(
                            "Nota de credito sem fatura de origem na BD principal; "
                            "nao e possivel reconstruir a ligacao na Community."))

                    # ---- Localizar a fatura original ja replicada no destino ----
                    src_origin = self.reversed_entry_id
                    dest_origin = second_env["account.move"]

                    # 1) Via direta: campo x_original_invoice_id (so se existir
                    #    no ORM do destino - depende de pg_bd_connection_fields
                    #    atualizado/instalado na Community).
                    field_exists = "x_original_invoice_id" in second_env["account.move"]._fields
                    if field_exists:
                        dest_origin = second_env["account.move"].sudo().search(
                            [("x_original_invoice_id", "=", src_origin.id)], limit=1)

                    # 2) Fallback por chave natural, para faturas sincronizadas
                    #    antes de o campo existir. Usa amount_untaxed (e nao o
                    #    total) porque as taxas sem match por nome sao ignoradas
                    #    no sync e o total pode divergir; o valor sem impostos
                    #    deriva diretamente das linhas replicadas.
                    if not dest_origin:
                        candidates = second_env["account.move"].sudo().search([
                            ("move_type", "=", src_origin.move_type),
                            ("partner_id.name", "=", src_origin.partner_id.name),
                            ("invoice_date", "=", src_origin.invoice_date),
                            ("amount_untaxed", "=", src_origin.amount_untaxed),
                            ("state", "=", "posted"),
                        ])
                        if len(candidates) == 1:
                            dest_origin = candidates
                            if field_exists:
                                # Backfill para acelerar/desambiguar no futuro.
                                dest_origin.sudo().x_original_invoice_id = src_origin.id
                        elif len(candidates) > 1:
                            raise ValueError(_(
                                "Encontradas %s faturas candidatas na Community para a "
                                "original '%s'. Defina a ligacao manualmente antes de "
                                "sincronizar a nota de credito."
                            ) % (len(candidates), src_origin.name or src_origin.id))

                    if not dest_origin:
                        raise ValueError(_(
                            "A fatura original '%s' ainda nao foi sincronizada/confirmada na "
                            "Community. Sincronize e confirme a fatura antes da nota de credito."
                        ) % (src_origin.name or src_origin.id))
                    if dest_origin.state != "posted":
                        raise ValueError(_(
                            "A fatura original '%s' esta em rascunho na Community. "
                            "Confirme-a antes de sincronizar a nota de credito."
                        ) % dest_origin.name)

                    # Motivo do estorno: o ref da NC origem ja vem no formato
                    # "Reversao de: <fatura>, <motivo>". Extrai-se so o <motivo>
                    # para a wizard nao duplicar o prefixo de reversao.
                    reason = self.ref or ""
                    orig_name = self.reversed_entry_id.name or ""
                    if orig_name and orig_name in reason:
                        reason = reason.split(orig_name, 1)[1].lstrip(", ").strip()

                    reversal = second_env["account.move.reversal"].sudo().with_context(
                        active_model="account.move",
                        active_ids=dest_origin.ids,
                    ).create({
                        "move_ids": [(6, 0, dest_origin.ids)],
                        "journal_id": dest_origin.journal_id.id,
                        "date": self.invoice_date or fields.Date.context_today(self),
                        "reason": reason,
                    })
                    # Cria a NC em rascunho no destino (a certificacao posta depois).
                    reversal.reverse_moves()
                    new_invoice = reversal.new_move_ids[:1]
                    if not new_invoice:
                        raise ValueError(_("A reversao na Community nao devolveu nenhum documento."))

                    # Alinha os valores das linhas com a NC origem (cobre NCs
                    # parciais / valores corrigidos). Mantem o origin_line_id
                    # criado pela reversao. Se a contagem divergir, nao se
                    # adivinha: mantem-se a reversao integral e regista-se aviso.
                    src_lines = self.invoice_line_ids.filtered(
                        lambda l: l.display_type not in ("line_section", "line_note")
                    ).sorted(lambda l: l.sequence)
                    dst_lines = new_invoice.invoice_line_ids.filtered(
                        lambda l: l.display_type not in ("line_section", "line_note")
                    ).sorted(lambda l: l.sequence)

                    if len(src_lines) != len(dst_lines):
                        _logger.warning(
                            "Refund %s: %s linha(s) na origem vs %s na reversao do "
                            "destino; valores nao alinhados automaticamente.",
                            self.name, len(src_lines), len(dst_lines))
                    else:
                        for s_line, d_line in zip(src_lines, dst_lines):
                            tax_ids = [
                                second_env["account.tax"].sudo().search(
                                    [("name", "=", tax.name)], limit=1).id
                                for tax in s_line.tax_ids
                                if second_env["account.tax"].sudo().search(
                                    [("name", "=", tax.name)], limit=1)
                            ]
                            d_line.sudo().write({
                                "name": s_line.name,
                                "quantity": s_line.quantity or 0.0,
                                "price_unit": s_line.price_unit or 0.0,
                                "discount": s_line.discount or 0.0,
                                "tax_ids": [(6, 0, tax_ids)] if tax_ids else [(5, 0, 0)],
                            })

                    _logger.info(
                        "Credit note replicated via reversal in Community: ID %s",
                        new_invoice.id)
                    self.sudo().write({"x_studio_community": True})
                    self.message_post(body=_("Credit note successfully synced (reversal linked)."))
                    return True

                # ---- Linhas: respeitar ordem por sequence ----
                invoice_lines = []
                for line in self.invoice_line_ids.sorted(lambda l: l.sequence):
                    # Sections e notes nao tem produto/conta; replicar so o nome.
                    if line.display_type in ["line_section", "line_note"]:
                        invoice_lines.append((0, 0, {
                            "display_type": line.display_type,
                            "name": line.name,
                            "sequence": line.sequence,
                        }))
                        continue

                    # Matching de taxes por nome - ignora silenciosamente as que
                    # nao existem na destino. Validar manualmente se faltarem.
                    tax_ids = [
                        second_env["account.tax"].sudo().search([("name", "=", tax.name)], limit=1).id
                        for tax in line.tax_ids
                        if second_env["account.tax"].sudo().search([("name", "=", tax.name)], limit=1)
                    ]

                    invoice_lines.append((0, 0, {
                        "name": line.name,
                        "quantity": line.quantity or 0.0,
                        "price_unit": line.price_unit or 0.0,
                        "discount": line.discount or 0.0,
                        "tax_ids": [(6, 0, tax_ids)] if tax_ids else [],
                        "account_id": account_id,
                        "sequence": line.sequence,
                    }))

                # ---- Endereco de entrega: replicar partner_shipping_id ----
                # Por defeito a entrega = cliente. Quando difere, procura-se
                # (ou cria-se) na BD destino um contacto de entrega
                # (type=delivery) filho do cliente. Os ids de distrito/estado
                # diferem entre BDs, por isso o estado e mapeado por nome.
                shipping = customer
                src_ship = self.partner_shipping_id
                if src_ship and src_ship.id != self.partner_id.id:
                    Partner = second_env["res.partner"].sudo()
                    ship = Partner.browse()
                    if src_ship.name:
                        ship = Partner.search(
                            [("name", "=", src_ship.name), ("parent_id", "=", customer.id)],
                            limit=1,
                        ) or Partner.search([("name", "=", src_ship.name)], limit=1)
                    if not ship:
                        state_id = False
                        if src_ship.state_id:
                            st_dom = [("name", "=", src_ship.state_id.name)]
                            if src_ship.country_id:
                                st_dom.append(("country_id", "=", src_ship.country_id.id))
                            st = second_env["res.country.state"].sudo().search(st_dom, limit=1)
                            state_id = st.id if st else False
                        ship = Partner.create({
                            "name": src_ship.name or (customer.name or "") + " - Entrega",
                            "type": "delivery",
                            "parent_id": customer.id,
                            "street": src_ship.street,
                            "street2": src_ship.street2,
                            "city": src_ship.city,
                            "zip": src_ship.zip,
                            "state_id": state_id,
                            "country_id": src_ship.country_id.id if src_ship.country_id else False,
                            "vat": src_ship.vat,
                        })
                    shipping = ship

                invoice_data = {
                    "partner_id": customer.id,
                    "partner_shipping_id": shipping.id,
                    "move_type": self.move_type,
                    "invoice_date": self.invoice_date,
                    "invoice_date_due": self.invoice_date_due,
                    "payment_reference": self.payment_reference,
                    "state": "draft",
                    "invoice_line_ids": invoice_lines,
                    "journal_id": journal.id,
                }

                # Preserva o id da fatura origem como contexto se o campo
                # existir na destino (depende de ``pg_bd_connection`` ja la estar).
                if "x_original_invoice_id" in second_env["account.move"]._fields:
                    invoice_data["x_original_invoice_id"] = self.id

                # Fatura-guia (ptplus): a "Descarga" IMPRESSA vem de
                # ``l10n_pt_unloading_partner_id`` (nao do partner_shipping_id).
                # Esse campo e readonly/gerido pelo ptplus (codigo encriptado) e
                # esta vazio em todas as faturas, por isso preenche-se aqui no
                # create - antes da assinatura/SAF-T - com a morada de entrega,
                # apenas quando difere do cliente (senao o template ja mostra o
                # fallback "Customer Address").
                # ATENCAO: campo de modulo certificado. VALIDAR num teste que o
                # ptplus mantem o valor apos posting (pode recomputa-lo) e que a
                # assinatura/SAF-T computa sem erro antes de confiar nisto.
                dest_move_fields = second_env["account.move"]._fields
                if ("l10n_pt_unloading_partner_id" in dest_move_fields
                        and shipping.id != customer.id):
                    invoice_data["l10n_pt_unloading_partner_id"] = shipping.id

                try:
                    new_invoice = second_env["account.move"].sudo().create(invoice_data)
                    _logger.info("Invoice successfully created in the second database: ID %s", new_invoice.id)

                    # Flag de "ja sincronizado" - campo Studio na origem.
                    self.sudo().write({"x_studio_community": True})

                    self.message_post(body=_("Invoice successfully synced."))
                    return True
                except Exception as e:
                    _logger.error("Failed to create invoice in the second database: %s", str(e))
                    raise ValueError(_("Failed to create invoice in the second database: %s") % str(e))

        except Exception as e:
            _logger.error("Failed to switch to second database: %s", str(e))
            raise ValueError(_("Could not access the second database: %s") % str(e))
