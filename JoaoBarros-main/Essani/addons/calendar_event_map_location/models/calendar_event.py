import logging

from odoo import api, fields, models


_logger = logging.getLogger(__name__)


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    partner_id = fields.Many2one(
        "res.partner",
        string="Contact",
        tracking=True,
        index=True,
        related=False,
        readonly=False,
        store=True,
        help="Primary contact associated with this meeting.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        users = self.env["res.users"]
        for vals in vals_list:
            if vals.get("partner_id"):
                continue
            user = False
            if vals.get("user_id"):
                user = users.browse(vals["user_id"])
            elif self.env.context.get("default_user_id"):
                user = users.browse(self.env.context["default_user_id"])
            if not user:
                user = self.env.user
            partner = user.partner_id if user else False
            if partner:
                vals.setdefault("partner_id", partner.id)
                _logger.debug(
                    "calendar.event create default partner set from user %s to partner %s",
                    user.id,
                    partner.id,
                )
            else:
                _logger.debug(
                    "calendar.event create no partner default for vals %s", vals
                )
        return super().create(vals_list)

    def write(self, vals):
        if "partner_id" not in vals and "user_id" in vals:
            partner = False
            if vals.get("user_id"):
                user = self.env["res.users"].browse(vals["user_id"])
                partner = user.partner_id
            if partner:
                vals = dict(vals, partner_id=partner.id)
                _logger.debug(
                    "calendar.event write sync partner to %s from user %s for records %s",
                    partner.id,
                    vals.get("user_id"),
                    self.ids,
                )
            else:
                vals = dict(vals, partner_id=False)
                _logger.debug(
                    "calendar.event write clearing partner because user has none for records %s",
                    self.ids,
                )
        elif "partner_id" in vals:
            _logger.debug(
                "calendar.event write explicit partner change to %s for records %s",
                vals.get("partner_id"),
                self.ids,
            )
        return super().write(vals)

    @api.onchange("user_id")
    def _onchange_user_id_set_partner(self):
        if self.user_id and not self.partner_id:
            self.partner_id = self.user_id.partner_id
            _logger.debug(
                "calendar.event onchange set partner %s from user %s for record %s",
                self.partner_id.id if self.partner_id else None,
                self.user_id.id,
                self.id,
            )
