from odoo import fields, models, api
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_fields_stock_barcode(self):
        fields = super()._get_fields_stock_barcode()
        fields.append('product_form')
        return fields

    thickness = fields.Float(
        string='Espessura',
        store=True,
        digits='Dimensions',
        help='Espessura em metros (independente do template)'
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Preencher thickness do template na criação da variante"""
        for vals in vals_list:
            # Se não tem thickness definido, pegar do template
            if 'thickness' not in vals or not vals.get('thickness'):
                template_id = vals.get('product_tmpl_id')
                if template_id:
                    template = self.env['product.template'].browse(template_id)
                    if template.thickness:
                        vals['thickness'] = template.thickness

        return super().create(vals_list)

    def write(self, vals):
        """Sincronizar thickness de volta ao template se for variante única"""
        result = super().write(vals)

        # Se thickness mudou e template tem apenas 1 variante, sincronizar
        if 'thickness' in vals and not self.env.context.get('skip_thickness_sync'):
            for product in self:
                template = product.product_tmpl_id
                if template and template.product_variant_count == 1:
                    # Variante única: sincronizar de volta ao template
                    template.with_context(skip_thickness_sync=True).write({'thickness': vals['thickness']})

        return result

    @api.constrains('product_form', 'thickness')
    def _check_thickness_required(self):
        """Valida thickness obrigatório para slab, strip, tiles"""
        for product in self:
            if product.product_form in ['slab', 'strip', 'tiles']:
                if not product.thickness or product.thickness <= 0:
                    form_names = {'slab': 'Placa', 'strip': 'Banda', 'tiles': 'Ladrilhos'}
                    form_name = form_names.get(product.product_form, product.product_form)
                    raise ValidationError(
                        f"[PRODUCT.PRODUCT]❌ Espessura obrigatória!\n\n"
                        f"Produtos do tipo '{form_name}' exigem espessura maior que zero.\n"
                        f"Por favor, informe a espessura do produto."
                    )
