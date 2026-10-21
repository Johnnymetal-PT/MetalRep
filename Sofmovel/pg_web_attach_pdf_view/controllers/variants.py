"""Override JSON-RPC do combination_info do website com desconto e carousel.

Pertence ao modulo `pg_web_attach_pdf_view`. Substitui a rota standard
`/website_sale/get_combination_info` para acrescentar `discount_percentage`
calculado a partir de `compare_list_price` e re-renderizar o carousel de
imagens via `website_sale.shop_product_images`.
"""
from odoo import http
from odoo.http import request


class WebsiteSaleVariantCustomController(http.Controller):
    """Endpoint JSON-RPC com combination_info enriquecido."""

    @http.route('/website_sale/get_combination_info', type='json', auth="public", website=True)
    def get_combination_info(self, **kwargs):
        product_template_id = int(kwargs.get("product_template_id", 0))
        combination = kwargs.get("combination", [])
        add_qty = float(kwargs.get("add_qty", 1.0))
        only_template = kwargs.get("only_template", False)
        parent_combination = kwargs.get("parent_combination", [])

        # Fetch the template and compute the combination info
        product_template = request.env['product.template'].sudo().browse(product_template_id)
        combination_info = product_template._get_combination_info(
            combination=combination,
            parent_combination=parent_combination,
            only_template=only_template,
            add_qty=add_qty
        )

        # Compute the discount
        list_price = combination_info.get("list_price")
        compare_price = combination_info.get("compare_list_price")

        if compare_price and list_price and compare_price > list_price:
            discount = round(((compare_price - list_price) / compare_price) * 100)
            combination_info["discount_percentage"] = discount
        else:
            combination_info["discount_percentage"] = 0

        # Prepare rendering context
        values = {
            "product": product_template,
            "product_variant": product_template.product_variant_id,
            "combination_info": combination_info,
            "add_qty": add_qty,
        }

        # Render product image carousel using shop_product_images template
        combination_info["carousel"] = request.env["ir.ui.view"]._render_template(
            "website_sale.shop_product_images", values
        )

        return combination_info

