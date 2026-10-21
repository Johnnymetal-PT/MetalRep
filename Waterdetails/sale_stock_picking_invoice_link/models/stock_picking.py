# Copyright 2013-17 Agile Business Group (<http://www.agilebg.com>)
# Copyright 2016 AvanzOSC (<http://www.avanzosc.es>)
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2017 Jacques-Etienne Baudoux <je@bcim.be>
# Copyright 2021 Tecnativa - João Marques
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    invoice_ids = fields.Many2many(
        comodel_name="account.move",
        string="Invoices",
        compute="_compute_invoice_ids",
        store=True,
        copy=False,
        readonly=True,
    )

    @api.depends("move_ids.invoice_line_ids.move_id")
    def _compute_invoice_ids(self):
        for picking in self:
            picking.invoice_ids = picking.mapped(
                "move_ids.invoice_line_ids.move_id"
            )
