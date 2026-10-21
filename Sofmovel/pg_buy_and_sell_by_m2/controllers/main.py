"""Controller do carrinho para o `pg_buy_and_sell_by_m2`.

Pertence ao modulo `pg_buy_and_sell_by_m2`. Recebe largura/comprimento do
formulario publico e regrava a linha do carrinho com quantidade = area e
price_unit = preco minimo do produto.
"""
from odoo import http
from odoo.http import request

class CustomCartController(http.Controller):
    """Endpoint publico de adicao ao carrinho com dimensoes em metros."""

    @http.route('/shop/cart/update_custom', type='http', auth='public', methods=['POST'], csrf=True)
    def cart_update_custom(self, product_id, x_studio_largura, x_studio_comprimento, **kwargs):
        # IMPORTANTE: remove linhas existentes do mesmo produto antes de criar
        # a nova. Implica que so e possivel uma combinacao por produto no
        # carrinho (deliberado: carpetes/alcatifas sao por encomenda unica).
        order = request.website.sale_get_order(force_create=True)
        product = request.env['product.product'].browse(int(product_id))

        try:
            largura = float(x_studio_largura)
            comprimento = float(x_studio_comprimento)
            area = largura * comprimento
        except Exception:
            return request.redirect('/shop/cart')

        # calcula o preço unitário baseado na lista de preços ativa
        price_info = product._get_combination_info(product.product_template_variant_ids[0])
        preco_unitario = price_info.get('min_price', product.list_price)
        preco_total = preco_unitario  # já é por m²

        if product and area > 0:
            # remove linhas existentes do mesmo produto
            order.order_line.filtered(lambda l: l.product_id.id == product.id).unlink()

            # cria a linha com quantidade = área, preço unitário calculado
            order.sudo().write({
                'order_line': [(0, 0, {
                    'product_id': product.id,
                    'name': f"{product.name} ({largura:.2f}m x {comprimento:.2f}m)",
                    'product_uom_qty': area,
                    'price_unit': preco_total,
                })]
            })

        return request.redirect('/shop/cart')

