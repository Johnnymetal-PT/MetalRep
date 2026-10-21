# -*- coding: utf-8 -*-
import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Campos que definem a "chave de fusão". Duas vendas só podem ser fundidas se
# forem iguais em TODOS estes campos ao mesmo tempo (decisão de âmbito com o
# cliente). Ver README do módulo.
MERGE_KEY_FIELDS = [
    "company_id",
    "partner_id",
    "partner_shipping_id",
    "partner_invoice_id",
    "pricelist_id",
    "currency_id",
    "fiscal_position_id",
    "payment_term_id",
]

# Acima deste número de vendas por fusão, exige confirmação explícita (evita
# fusões acidentais de grupos gigantes, ex.: backlog intercompany).
LARGE_MERGE_THRESHOLD = 20


class SaleOrder(models.Model):
    _inherit = "sale.order"

    pg_merged_into_id = fields.Many2one(
        comodel_name="sale.order",
        string="Fundida em",
        readonly=True,
        copy=False,
        index=True,
        help="Preenchido quando esta venda foi incorporada noutra através da "
        "fusão PG. A venda de origem fica cancelada.",
    )
    pg_merge_source_ids = fields.One2many(
        comodel_name="sale.order",
        inverse_name="pg_merged_into_id",
        string="Vendas incorporadas",
        readonly=True,
        help="Vendas que foram incorporadas nesta através da fusão PG.",
    )

    # ------------------------------------------------------------------
    # Helpers de elegibilidade
    # ------------------------------------------------------------------
    def _pg_merge_key(self):
        """Devolve o tuplo que identifica a chave de fusão desta venda."""
        self.ensure_one()
        return tuple(self[f].id if self[f] else False for f in MERGE_KEY_FIELDS)

    def _pg_is_intercompany(self):
        """True se o cliente da venda for uma empresa do próprio grupo
        (padrão típico das vendas intercompany, ex.: Oficinna 22 -> Triplex)."""
        self.ensure_one()
        company_partners = self.env["res.company"].sudo().search([]).mapped(
            "partner_id"
        )
        return (
            self.partner_id in company_partners
            or self.partner_id.commercial_partner_id in company_partners
        )

    def _pg_assert_pre_logistics(self):
        """Garante que uma venda confirmada ainda não executou logística.
        Cotações (draft/sent) não têm logística, passam sempre."""
        self.ensure_one()
        if self.state != "sale":
            return
        if self.picking_ids.filtered(lambda p: p.state == "done"):
            raise UserError(
                _("A venda %s já tem entregas concluídas; não pode ser fundida.")
                % self.name
            )
        if self.invoice_ids.filtered(lambda m: m.state == "posted"):
            raise UserError(
                _("A venda %s já tem faturas publicadas; não pode ser fundida.")
                % self.name
            )
        group = self.procurement_group_id
        if group:
            if "mrp.production" in self.env:
                mo = self.env["mrp.production"].search(
                    [
                        ("procurement_group_id", "=", group.id),
                        ("state", "in", ("progress", "to_close", "done")),
                    ],
                    limit=1,
                )
                if mo:
                    raise UserError(
                        _(
                            "A venda %s tem ordens de produção em curso/concluídas; "
                            "não pode ser fundida."
                        )
                        % self.name
                    )
            if "purchase.order" in self.env:
                pos = self.env["purchase.order"].search(
                    [("group_id", "=", group.id)]
                )
                if any(p.receipt_status in ("partial", "full") for p in pos):
                    raise UserError(
                        _(
                            "A venda %s tem compras já rececionadas; não pode ser "
                            "fundida."
                        )
                        % self.name
                    )

    def _pg_assert_mergeable(self):
        """Validações comuns a todo o conjunto selecionado."""
        if len(self) < 2:
            raise UserError(_("Selecione pelo menos duas vendas para fundir."))
        if any(o.state == "cancel" for o in self):
            raise UserError(_("Não é possível fundir vendas canceladas."))
        if any(o.state not in ("draft", "sent", "sale") for o in self):
            raise UserError(
                _(
                    "Só é possível fundir vendas em Cotação/Cotação Enviada ou "
                    "Confirmadas."
                )
            )
        if any(o.pg_merged_into_id for o in self):
            raise UserError(
                _("Uma das vendas selecionadas já foi fundida noutra.")
            )
        keys = {o._pg_merge_key() for o in self}
        if len(keys) != 1:
            raise UserError(
                _(
                    "As vendas selecionadas não partilham a mesma chave de fusão "
                    "(empresa, cliente, endereço de entrega, endereço de faturação, "
                    "lista de preços, moeda, posição fiscal e condições de "
                    "pagamento têm de ser iguais em todas)."
                )
            )
        for order in self:
            order._pg_assert_pre_logistics()

    # ------------------------------------------------------------------
    # Religação de logística (apenas vendas confirmadas)
    # ------------------------------------------------------------------
    def _pg_relink_downstream(self, sources):
        """Re-aponta entregas, ordens de produção e compras das vendas de
        origem para o grupo de procurement da sobrevivente, para que a
        logística fique ligada à venda única.

        NOTA: caminho de vendas confirmadas — validar com um caso confirmado
        real antes de uso em produção (as cotações de teste não exercitam
        este código)."""
        self.ensure_one()
        confirmed_sources = sources.filtered(lambda o: o.state == "sale")
        if not confirmed_sources:
            return
        target_group = self.procurement_group_id
        if not target_group:
            raise UserError(
                _(
                    "A venda sobrevivente %s não tem grupo de procurement; para "
                    "fundir vendas confirmadas a sobrevivente tem de ser uma venda "
                    "confirmada."
                )
                % self.name
            )
        old_groups = confirmed_sources.mapped("procurement_group_id") - target_group
        for grp in old_groups:
            self.env["stock.move"].search(
                [("group_id", "=", grp.id)]
            ).write({"group_id": target_group.id})
            self.env["stock.picking"].search(
                [("group_id", "=", grp.id)]
            ).write({"group_id": target_group.id})
            if "mrp.production" in self.env:
                self.env["mrp.production"].search(
                    [("procurement_group_id", "=", grp.id)]
                ).write({"procurement_group_id": target_group.id})
            if "purchase.order" in self.env:
                self.env["purchase.order"].search(
                    [("group_id", "=", grp.id)]
                ).write({"group_id": target_group.id})
            _logger.info(
                "PG merge: grupo %s re-apontado para %s (venda %s)",
                grp.name,
                target_group.name,
                self.name,
            )

    # ------------------------------------------------------------------
    # Ação principal
    # ------------------------------------------------------------------
    def action_pg_merge_orders(self):
        """Funde as vendas selecionadas numa só (padrão sobrevivente +
        mover linhas). Disparada pela ação contextual da lista de Vendas."""
        self._pg_assert_mergeable()

        if not self.env.context.get("pg_allow_intercompany"):
            inter = self.filtered(lambda o: o._pg_is_intercompany())
            if inter:
                raise UserError(
                    _(
                        "As vendas %s são intercompany (cliente = empresa do "
                        "grupo). A fusão intercompany está desativada por "
                        "defeito; trate-a à parte."
                    )
                    % ", ".join(inter.mapped("name"))
                )

        if len(self) > LARGE_MERGE_THRESHOLD and not self.env.context.get(
            "pg_confirm_large_merge"
        ):
            raise UserError(
                _(
                    "Vai fundir %d vendas numa só. Por segurança, esta operação "
                    "de grupo grande exige confirmação explícita."
                )
                % len(self)
            )

        # Sobrevivente = venda de id mais baixo (cotação/encomenda mais antiga).
        survivor = self.sorted("id")[0]
        sources = self - survivor

        source_lines = sources.mapped("order_line")
        if source_lines:
            source_lines.write({"order_id": survivor.id})

        survivor._pg_relink_downstream(sources)

        sources.write({"pg_merged_into_id": survivor.id})
        for src in sources:
            src.message_post(
                body=_("Fusão PG: linhas movidas para %s; esta venda foi cancelada.")
                % survivor.name
            )
        # Cancelar as origens (mantém registo e número em "Cancelados").
        sources._action_cancel()

        survivor.message_post(
            body=_("Fusão PG: incorporadas as vendas %s.")
            % ", ".join(sources.mapped("name"))
        )
        _logger.info(
            "PG merge concluído: %s <- %s",
            survivor.name,
            ", ".join(sources.mapped("name")),
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Venda fundida"),
            "res_model": "sale.order",
            "res_id": survivor.id,
            "view_mode": "form",
            "views": [(False, "form")],
            "target": "current",
        }
