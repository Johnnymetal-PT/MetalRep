# -*- coding: utf-8 -*-
"""Sincronizacao do flag 'Imprimir Imagens' do cabecalho da PO para as linhas.

Campos hardcoded vindos de Studio:
- `purchase.order.x_studio_imprimir_todas_imagens` (cabecalho)
- `purchase.order.line.x_studio_imprimir_imagem` (por linha)
- `purchase.order.line.x_studio_imagem_de_produto` (anexo binario)

Ver `__manifest__.py` para o guia completo.
"""

from odoo import api, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.onchange("x_studio_imprimir_todas_imagens")
    def _onchange_print_all_images(self):
        # UI path: utilizador clica no toggle. Se ligar, ativa por linha
        # APENAS se a linha tiver imagem (`x_studio_imagem_de_produto`).
        # Se desligar, limpa todas as linhas.
        if self.x_studio_imprimir_todas_imagens in (True, False):
            for line in self.order_line:
                if self.x_studio_imprimir_todas_imagens:
                    line.x_studio_imprimir_imagem = bool(line.x_studio_imagem_de_produto)
                else:
                    line.x_studio_imprimir_imagem = False

    def write(self, vals):
        # Persistencia: deteta mudanca no flag de cabecalho e sincroniza
        # APENAS as linhas que ainda estavam alinhadas com o estado
        # antigo - edicoes manuais por linha sao preservadas.
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

                # So atualizamos linhas que ainda tinham o valor antigo.
                # Linhas com valor diferente foram alteradas manualmente
                # e nao queremos sobrepor.
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
