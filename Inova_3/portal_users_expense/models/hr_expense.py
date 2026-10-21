# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import fields, models


class HrExpense(models.Model):
    _name = "hr.expense"
    _inherit = ["hr.expense", "portal.mixin"]

    access_url = fields.Char('Portal Access URL', compute='_compute_access_url', help='Expense Portal URL')

    def _compute_access_url(self):
        for expense in self:
            expense.access_url = '/my/expense/%s' % (expense.id)

    def _get_report_base_filename(self):
        self.ensure_one()
        return 'expense'

    def update_account_details(self):
        self.ensure_one()
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id
            self.tax_ids = self.product_id.supplier_taxes_id
            account = self.product_id.product_tmpl_id._get_product_accounts()['expense']
            if account:
                self.account_id = account
