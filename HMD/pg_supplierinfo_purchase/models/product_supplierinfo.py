# -*- coding: utf-8 -*-
"""Botao "Create RFQ" na linha de fornecedor (`product.supplierinfo`).

Monta a PO a partir da linha de supplierinfo: fornecedor, produto,
preco, UoM, delay, descontos e taxas - tudo defensivo (testa se cada
campo existe no schema, porque podem vir de modulos opcionais).

Ver `__manifest__.py` para o guia completo.
"""

from dateutil.relativedelta import relativedelta

from odoo import _, fields, models
from odoo.exceptions import UserError


class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"

    # Shim: existe so para nao partir views Studio que referenciam
    # purchase_requisition_id quando o modulo purchase_requisition NAO
    # esta instalado. Sem comportamento. Remover quando as views Studio
    # forem limpas.
    purchase_requisition_id = fields.Many2one(
        "purchase.requisition",
        string="Agreement",
    )

    def action_create_purchase_order(self):
        """Cria uma PO em draft a partir desta linha de fornecedor e abre o form."""
        self.ensure_one()

        vendor = self.partner_id or getattr(self, "name", False)
        if not vendor:
            raise UserError(
                _("Please define a vendor on the vendor list line before creating a purchase order."),
            )

        product = self.product_id or self.product_tmpl_id.product_variant_id
        if not product:
            raise UserError(
                _("Please link the vendor line to a product before creating a purchase order."),
            )

        company = self.company_id or self.env.company
        qty = self.min_qty or 1.0

        if "product_uom" in self._fields and self.product_uom:
            uom = self.product_uom
        else:
            uom = product.uom_po_id or product.uom_id
        if not uom:
            raise UserError(
                _("Please configure a purchase unit of measure for the selected product."),
            )

        planned_date = fields.Datetime.now()
        if "delay" in self._fields and self.delay:
            planned_date += relativedelta(days=int(self.delay))

        product_lang = product.with_context(
            lang=vendor.lang or self.env.user.lang,
            partner_id=vendor.id,
            company_id=company.id,
        )
        product_description = product_lang.with_context(seller_id=self.id).display_name
        if product_lang.description_purchase:
            product_description += "\n" + product_lang.description_purchase

        line_vals = {
            "product_id": product.id,
            "name": product_description,
            "product_qty": qty,
            "price_unit": self.price or 0.0,
            "product_uom": uom.id,
            "date_planned": planned_date,
        }
        if "discount" in self._fields:
            line_vals["discount"] = self.discount or 0.0
        if "taxes_id" in self._fields and self.taxes_id:
            line_vals["taxes_id"] = [(6, 0, self.taxes_id.ids)]

        order_currency = False
        if "currency_id" in self._fields and self.currency_id:
            order_currency = self.currency_id
        else:
            order_currency = vendor.property_purchase_currency_id or company.currency_id

        order_vals = {
            "partner_id": vendor.id,
            "company_id": company.id,
            "order_line": [(0, 0, line_vals)],
        }
        if order_currency:
            order_vals["currency_id"] = order_currency.id

        purchase = self.env["purchase.order"].with_company(company).create(order_vals)

        return {
            "type": "ir.actions.act_window",
            "name": _("Purchase Order"),
            "res_model": "purchase.order",
            "res_id": purchase.id,
            "view_mode": "form",
        }
