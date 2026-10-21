from odoo import fields, models, api
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    thickness = fields.Float(
        string='Espessura',
        digits='Dimensions',
        help='Espessura em metros'
    )

    def write(self, vals):
        """Sincronizar thickness para variante única"""
        result = super().write(vals)

        # Se thickness mudou e template tem apenas 1 variante, sincronizar
        if 'thickness' in vals and not self.env.context.get('skip_thickness_sync'):
            for template in self:
                if template.product_variant_count == 1:
                    # Template com variante única: sincronizar automaticamente
                    variant = template.product_variant_ids
                    if variant:
                        variant.with_context(skip_thickness_sync=True).write({'thickness': vals['thickness']})

        return result

    @api.constrains('product_form', 'thickness')
    def _check_thickness_required(self):
        """Valida thickness obrigatório para slab, strip, tiles"""
        for template in self:
            if template.product_form in ['slab', 'strip', 'tiles']:
                if not template.thickness or template.thickness <= 0:
                    form_names = {'slab': 'Placa', 'strip': 'Banda', 'tiles': 'Ladrilhos'}
                    form_name = form_names.get(template.product_form, template.product_form)
                    raise ValidationError(
                        f"[PRODUCT.TEMPLATE]❌ Espessura obrigatória!\n\n"
                        f"Produtos do tipo '{form_name}' exigem espessura maior que zero.\n"
                        f"Por favor, informe a espessura do produto."
                    )
