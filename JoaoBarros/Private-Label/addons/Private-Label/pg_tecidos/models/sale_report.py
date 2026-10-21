from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    salesperson_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Salesperson",
        readonly=True,
    )

    def _query(self, with_clause="", fields=None, groupby="", from_clause=""):
        if fields is None:
            fields = {}
        fields["salesperson_partner_id"] = ", s.salesperson_partner_id as salesperson_partner_id"
        groupby += ", s.salesperson_partner_id"
        try:
            return super()._query(with_clause, fields, groupby, from_clause)
        except TypeError:
            # Odoo 17+ signature: _query(self)
            return super()._query()

    def _select_additional_fields(self):
        res = {}
        if hasattr(super(), "_select_additional_fields"):
            res = super()._select_additional_fields()
        res["salesperson_partner_id"] = "s.salesperson_partner_id"
        return res

    def _group_by(self):
        if hasattr(super(), "_group_by"):
            groupby = super()._group_by()
            return groupby + ", s.salesperson_partner_id"
        return "s.salesperson_partner_id"

