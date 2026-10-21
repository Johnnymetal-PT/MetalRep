# -*- coding: utf-8 -*-
"""Botões de impressão de etiquetas/documentos A4 em vários modelos.

NOTA: por copy-paste, várias classes abaixo chamam-se "StockPicking" embora herdem de
modelos diferentes (product.template, product.product, stock.picking). O nome da classe
Python é irrelevante para o Odoo — o que liga ao modelo é o `_inherit`. Os relatórios
são procurados pelo nome visível, exceto na venda (procurados por report_name Studio).
Ver o __manifest__.py.
"""
from odoo import models

class StockPicking(models.Model):
    _inherit = 'product.template'

    def action_print_a4_report(self):
        # Procura o relatório pelo NOME visível e imprime-o para o registo atual.
        report = self.env['ir.actions.report'].search([('name', '=', 'Etiquetas A4')], limit=1)
        return report.report_action(self)



class StockPicking(models.Model):
    _inherit = 'product.product'

    def action_print_a4_report(self):
        # Mesma etiqueta "Etiquetas A4", agora a partir da variante de produto.
        report = self.env['ir.actions.report'].search([('name', '=', 'Etiquetas A4')], limit=1)
        return report.report_action(self)



class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_print_a4_report(self):
        # A partir do picking usa-se "Etiqueta A4" (singular) — relatório distinto do produto.
        report = self.env['ir.actions.report'].search([('name', '=', 'Etiqueta A4')], limit=1)
        return report.report_action(self)

    def action_print_a4_report_mythica(self):
        # Variante "Mythica" da etiqueta de picking.
        report = self.env['ir.actions.report'].search([('name', '=', 'Etiqueta Mythica A4')], limit=1)
        return report.report_action(self)


from odoo import models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_print_a4_report(self):
        # Na venda imprime-se um relatório criado via Odoo Studio, identificado pelo
        # report_name técnico (UUID gerado pelo Studio) — fixo neste código.
        report = self.env['ir.actions.report'].search([
            ('report_name', '=', 'studio_customization.studio_report_docume_93ca904d-bd32-4f00-842d-a202961be350'),
            ('model', '=', 'sale.order'),
        ], limit=1)
        return report.report_action(self)


    def action_print_a4_report_mythica(self):
        # Variante "Mythica" do documento de venda (outro relatório Studio).
        report = self.env['ir.actions.report'].search([
            ('report_name', '=', 'studio_customization.studio_report_docume_78594e7c-93c4-4f64-841b-8a2622da2b1b'),
            ('model', '=', 'sale.order'),
        ], limit=1)
        return report.report_action(self)

