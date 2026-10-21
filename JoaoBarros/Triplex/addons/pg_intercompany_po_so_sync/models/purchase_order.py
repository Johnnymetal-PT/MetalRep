from odoo import _, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @staticmethod
    def _can_create_sale_order(sale_order_model):
        if hasattr(sale_order_model, "has_access"):
            return sale_order_model.has_access("create")
        return sale_order_model.check_access_rights("create", raise_exception=False)

    @staticmethod
    def _should_auto_confirm_intercompany_document(company):
        if "intercompany_document_state" not in company._fields:
            return False
        return company.intercompany_document_state == "posted"

    def inter_company_create_sale_order(self, company):
        """Create an intercompany SO while preserving PO line data."""
        intercompany_uid = company.intercompany_user_id.id if company.intercompany_user_id else False
        if not intercompany_uid:
            raise UserError(_(
                "Provide at least one user for inter company relation for %(name)s",
                name=company.name,
            ))
        sale_order_model = self.env["sale.order"].with_user(intercompany_uid)
        if not self._can_create_sale_order(sale_order_model):
            raise UserError(_(
                "Inter company user of company %(name)s doesn't have enough access rights",
                name=company.name,
            ))

        for rec in self:
            company_partner = rec.company_id.partner_id.with_user(intercompany_uid)
            if (
                company_partner.property_product_pricelist
                and rec.currency_id.id != company_partner.property_product_pricelist.currency_id.id
            ):
                raise UserError(_(
                    "You cannot create SO from PO because sale price list currency is different "
                    "than purchase price list currency.\n"
                    "The currency of the SO is obtained from the pricelist of the company partner.\n\n"
                    "(SO currency: %(so_currency)s, Pricelist: %(pricelist)s, Partner: %(partner)s (ID: %(id)s))",
                    so_currency=rec.currency_id.name,
                    pricelist=company_partner.property_product_pricelist.display_name,
                    partner=company_partner.display_name,
                    id=company_partner.id,
                ))

            sale_order_data = rec.sudo()._prepare_sale_order_data(
                rec.name,
                company_partner,
                company,
                rec.dest_address_id.id or False,
            )
            source_lines = rec.order_line.sudo()
            for line in source_lines:
                sale_order_data["order_line"] += [(0, 0, rec._prepare_sale_order_line_data(line, company))]

            sale_order = (
                self.env["sale.order"]
                .with_context(
                    allowed_company_ids=company.ids,
                    in_rental_app=False,
                )
                .with_user(intercompany_uid)
                .create(sale_order_data)
            )
            sale_order_lines = sale_order.order_line.sorted(lambda line: (line.sequence, line.id))
            source_lines = source_lines.sorted(lambda line: (line.sequence, line.id))
            for source_line, sale_line in zip(source_lines, sale_order_lines):
                if source_line.name and sale_line.name != source_line.name:
                    sale_line.write({"name": source_line.name})
            msg = _(
                "Automatically generated from %(origin)s of company %(company)s.",
                origin=self.name,
                company=rec.company_id.name,
            )
            sale_order.message_post(body=msg)

            if not rec.partner_ref:
                rec.partner_ref = sale_order.name

            if self._should_auto_confirm_intercompany_document(company):
                sale_order.with_user(intercompany_uid).action_confirm()

    def _prepare_sale_order_line_data(self, line, company):
        res = super()._prepare_sale_order_line_data(line, company)
        if line.attachment_ids:
            res["attachment_ids"] = [(6, 0, line.attachment_ids.ids)]
        return res
