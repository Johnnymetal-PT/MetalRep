# -*- coding: utf-8 -*-
"""Botões de impressão dos catálogos de produto em PDF (várias versões/mercados).

Cada método dispara a ação de relatório correspondente. Ver o __manifest__.py.
"""
from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def compute_catalog_prices(self):
        """INCOMPLETO: devolve sempre uma lista vazia (código não terminado).

        Foi pensado para calcular os primeiros price_extra não-nulos, mas atualmente não
        produz resultado. O cálculo de preços no catálogo é feito nos templates QWeb.
        """
        self.ensure_one()
        price_extras = self.env['product.template.attribute.value'].search([
            ('product_tmpl_id', '=', self.id),
            ('price_extra', '!=', 0)
        ], order='price_extra asc')

        list_price = self.list_price
        prices = []

        return prices

    def action_print_catalog(self):
        """ Generates the product catalog PDF report for multiple selected products. """
        if not self:
            raise ValueError("No products selected for catalog printing.")
        
        return self.env.ref('pg_catalog.product_template_report_action').report_action(self)

    def action_print_catalog_255(self):
        """ Generates the 255 version of the Product Catalog PDF. """
        if not self:
            raise ValueError("No products selected for catalog printing (255).")
        return self.env.ref('pg_catalog.product_template_report_action_255').report_action(self)

    def action_print_catalog_usa(self):
        """ Generates the USA version of the Product Catalog PDF. """
        if not self:
            raise ValueError("No products selected for catalog printing (USA).")
        return self.env.ref('pg_catalog.product_template_report_action_usa').report_action(self)
        
    def action_print_catalog_maisondoree(self):
        """ Generates the Maison Dorée version of the Product Catalog PDF. """
        if not self:
            raise ValueError("No products selected for catalog printing (Maison Dorée).")
        return self.env.ref('pg_catalog.product_template_report_action_maisondoree').report_action(self)
        
    def action_print_catalog_usaeur(self):
        """ Generates the USA - EUR version of the Product Catalog PDF. """
        if not self:
            raise ValueError("No products selected for catalog printing (USA - EUR).")
        return self.env.ref('pg_catalog.product_template_report_action_usaeur').report_action(self)
        
    def action_print_catalog_usaeur16(self):
        """ Generates the USA - EUR 16 version of the Product Catalog PDF. """
        if not self:
            raise ValueError("No products selected for catalog printing (USA - EUR 16).")
        return self.env.ref('pg_catalog.product_template_report_action_usaeur16').report_action(self)

    def action_print_catalog_net2026(self):
        """ Generates the NET 2026 version (price x 2.35) of the Product Catalog PDF. """
        if not self:
            raise ValueError("No products selected for catalog printing (NET 2026).")
        return self.env.ref('pg_catalog.product_template_report_action_net2026').report_action(self)

    def action_print_catalog_netdisplay2026(self):
        """ Generates the NET DISPLAY 2026 version (price x 1.90) of the Product Catalog PDF. """
        if not self:
            raise ValueError("No products selected for catalog printing (NET DISPLAY 2026).")
        return self.env.ref('pg_catalog.product_template_report_action_netdisplay2026').report_action(self)
