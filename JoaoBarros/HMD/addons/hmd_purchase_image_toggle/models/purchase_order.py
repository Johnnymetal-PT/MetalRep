from odoo import api, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.onchange("x_studio_imprimir_todas_imagens")
    def _onchange_print_all_images(self):
        if self.x_studio_imprimir_todas_imagens in (True, False):
            for line in self.order_line:
                if self.x_studio_imprimir_todas_imagens:
                    line.x_studio_imprimir_imagem = bool(line.x_studio_imagem_de_produto)
                else:
                    line.x_studio_imprimir_imagem = False

    def write(self, vals):
        apply_sync = "x_studio_imprimir_todas_imagens" in vals
        if apply_sync:
            previous_headers = {order.id: order.x_studio_imprimir_todas_imagens for order in self}
            previous_line_flags = {
                line.id: line.x_studio_imprimir_imagem for line in self.mapped("order_line")
            }

        result = super().write(vals)

        if apply_sync:
            new_value = vals.get("x_studio_imprimir_todas_imagens")
            for order in self:
                old_value = previous_headers.get(order.id)
                if old_value is None or old_value == new_value:
                    continue

                lines_to_update = order.order_line.filtered(
                    lambda line: previous_line_flags.get(line.id, line.x_studio_imprimir_imagem)
                    == old_value
                )
                if lines_to_update:
                    values = {
                        line.id: (new_value and bool(line.x_studio_imagem_de_produto))
                        or False
                        for line in lines_to_update
                    }
                    for line in lines_to_update:
                        line.write({"x_studio_imprimir_imagem": values[line.id]})

        return result
