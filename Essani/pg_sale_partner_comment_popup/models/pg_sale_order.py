# -*- coding: utf-8 -*-
"""Aviso em orcamentos que mostra o comentario do contacto selecionado."""

from odoo import api, models, _
from odoo.tools import html2plaintext


class PgSaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange("partner_id")
    def _pg_onchange_partner_id_comment_warning(self):
        partner = self.partner_id
        if not partner or not partner.comment:
            return

        pg_comment_message = html2plaintext(partner.comment or "").strip()
        if not pg_comment_message:
            return

        return {
            "warning": {
                "title": _("Contact Comment"),
                "message": _(
                    "Comment registered for %(partner_name)s:\n\n%(comment)s",
                    partner_name=partner.display_name,
                    comment=pg_comment_message,
                ),
            }
        }
