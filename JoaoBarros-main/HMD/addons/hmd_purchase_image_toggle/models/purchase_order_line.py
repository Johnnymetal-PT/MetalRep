from odoo import api, models
from odoo.exceptions import ValidationError


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.constrains("x_studio_imprimir_imagem", "x_studio_imagem_de_produto")
    def _check_image_flag_requires_attachment(self):
        for line in self:
            if line.x_studio_imprimir_imagem and not line.x_studio_imagem_de_produto:
                raise ValidationError(
                    "A imagem deve estar definida para permitir a impressão da imagem."
                )
