# -*- coding: utf-8 -*-
"""Imagem da linha de venda preenchida UMA VEZ a partir do produto.

O campo Studio `x_studio_imagem_do_produto` recebe o default da imagem
do produto na primeira vez que o produto e definido. Edicoes manuais
sao detetadas (comparando com o default atual) e marcadas com a flag
`hmd_sale_product_image_manual` - a partir dai nao se sobrepoe.

Ver `__manifest__.py` para o guia completo, incluindo a dependencia
do campo Studio.
"""

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    # Ponto unico de configuracao - mexer aqui se o Studio renomear o
    # campo de imagem ou se quisermos mover para campo nao-Studio.
    _sale_line_image_field = "x_studio_imagem_do_produto"
    _sale_line_image_manual_field = "hmd_sale_product_image_manual"
    _product_image_fields = (
        "image_1920",
        "image_1024",
        "image_512",
        "image_256",
        "image_128",
    )

    x_studio_imagem_do_produto = fields.Binary(
        string="Imagem do Produto",
        copy=False,
        help="Defaults from the selected product once, then remains editable.",
    )
    hmd_sale_product_image_manual = fields.Boolean(
        string="Product Image Manually Changed",
        default=False,
        copy=False,
        help="Technical flag used to preserve manual changes to the line image.",
    )

    def _get_default_sale_line_image(self, product=None):
        self.ensure_one()
        product = product or self.product_id
        if not product:
            return False

        for record in (product, product.product_tmpl_id):
            if not record:
                continue
            for field_name in self._product_image_fields:
                if field_name in record._fields and record[field_name]:
                    return record[field_name]
        return False

    def _is_manual_sale_line_image(self, image_value, product=None):
        self.ensure_one()
        return image_value != self._get_default_sale_line_image(product=product)

    def _set_default_sale_line_image(self):
        image_field = self._sale_line_image_field
        manual_field = self._sale_line_image_manual_field

        for line in self:
            if not line.product_id or line[manual_field]:
                continue

            line[image_field] = line._get_default_sale_line_image()
            line[manual_field] = False

    def _sync_sale_line_image_manual_flag(self):
        image_field = self._sale_line_image_field
        manual_field = self._sale_line_image_manual_field

        for line in self:
            manual_value = line._is_manual_sale_line_image(line[image_field])
            if line[manual_field] != manual_value:
                line[manual_field] = manual_value

    @api.onchange("product_id")
    def _onchange_product_id_set_sale_line_image(self):
        for line in self:
            if not line.product_id or line[line._sale_line_image_manual_field]:
                continue
            line._set_default_sale_line_image()

    @api.onchange("x_studio_imagem_do_produto")
    def _onchange_sale_line_image_mark_manual(self):
        self._sync_sale_line_image_manual_flag()

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._set_default_sale_line_image()
        lines._sync_sale_line_image_manual_flag()
        return lines

    def write(self, vals):
        image_field = self._sale_line_image_field
        manual_field = self._sale_line_image_manual_field

        if image_field in vals and manual_field not in vals:
            result = True
            for line in self:
                line_vals = dict(vals)
                if line[manual_field]:
                    line_vals.pop(image_field, None)
                if line_vals:
                    result = super(SaleOrderLine, line).write(line_vals) and result
            if image_field not in vals or manual_field in vals or "product_id" in vals:
                self._sync_sale_line_image_manual_flag()
            return result

        result = super().write(vals)

        if "product_id" in vals and image_field not in vals and manual_field not in vals:
            self._set_default_sale_line_image()

        if image_field in vals or "product_id" in vals or manual_field in vals:
            self._sync_sale_line_image_manual_flag()

        return result

