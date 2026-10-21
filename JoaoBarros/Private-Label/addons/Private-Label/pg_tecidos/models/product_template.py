# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    name_en_us = fields.Char(
        string="Name (EN)",
        compute="_compute_name_translations",
        inverse="_inverse_name_en_us",
        store=False,
    )
    name_pt_pt = fields.Char(
        string="Name (PT)",
        compute="_compute_name_translations",
        inverse="_inverse_name_pt_pt",
        store=False,
    )

    @api.depends("name")
    def _compute_name_translations(self):
        for record in self:
            record.name_en_us = record.with_context(lang="en_US").name or False
            record.name_pt_pt = record.with_context(lang="pt_PT").name or False

    def _inverse_name_en_us(self):
        for record in self:
            record.with_context(lang="en_US").name = record.name_en_us or False

    def _inverse_name_pt_pt(self):
        for record in self:
            record.with_context(lang="pt_PT").name = record.name_pt_pt or False
