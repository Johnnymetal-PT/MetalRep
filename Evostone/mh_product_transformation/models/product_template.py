from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # NOTA: product_form é definido em mh_inventory (evitar dependência circular)

    can_be_transformed = fields.Boolean(
        string='Pode ser Transformado',
        help='Indica se este produto pode ser transformado'
    )

    @api.onchange('product_form')
    def _onchange_product_form(self):
        """Define automaticamente a unidade de medida baseada no tipo de produto"""
        if self.product_form == 'block':
            # Bloco = m³
            uom_cubic = self.env.ref('uom.product_uom_cubic_meter', raise_if_not_found=False)
            if uom_cubic:
                self.uom_id = uom_cubic
                self.uom_po_id = uom_cubic
        elif self.product_form in ['slab', 'strip', 'tiles']:
            # Placa, Banda, Ladrilhos = m²
            uom_square = self.env.ref('uom.uom_square_meter', raise_if_not_found=False)
            if uom_square:
                self.uom_id = uom_square
                self.uom_po_id = uom_square
        elif self.product_form == 'none':
            # Nenhum = desmarca can_be_transformed
            self.can_be_transformed = False

        # Forçar produto estocável com rastreamento por lote
        if self.product_form != 'none':
            self.is_storable = True
            self.tracking = 'lot'

    @api.constrains('product_form', 'uom_id')
    def _check_uom_compatibility(self):
        """Valida se a unidade de medida é compatível com a forma do produto"""
        uom_cubic = self.env.ref('uom.product_uom_cubic_meter', raise_if_not_found=False)
        uom_square = self.env.ref('uom.uom_square_meter', raise_if_not_found=False)

        for template in self:
            if template.product_form == 'block' and template.uom_id != uom_cubic:
                raise ValidationError(
                    "Produtos do tipo 'Bloco' só podem usar a unidade de medida m³ (metro cúbico)."
                )
            elif template.product_form in ['slab', 'strip', 'tiles'] and template.uom_id != uom_square:
                form_names = {'slab': 'Placa', 'strip': 'Banda', 'tiles': 'Ladrilhos'}
                form_name = form_names.get(template.product_form, template.product_form)
                raise ValidationError(
                    f"Produtos do tipo '{form_name}' só podem usar a unidade de medida m² (metro quadrado)."
                )

    @api.constrains('product_form', 'is_storable', 'tracking')
    def _check_tracking_required(self):
        """Valida que produtos com forma específica são estocáveis com rastreamento por lote"""
        for template in self:
            if template.product_form != 'none':
                if not template.is_storable:
                    form_names = {'block': 'Bloco', 'slab': 'Placa', 'strip': 'Banda', 'tiles': 'Ladrilhos'}
                    form_name = form_names.get(template.product_form, template.product_form)
                    raise ValidationError(
                        f"❌ Produto deve ser estocável!\n\n"
                        f"Produtos do tipo '{form_name}' devem ser produtos estocáveis.\n"
                        f"Por favor, marque 'Pode ser estocado'."
                    )

                if template.tracking != 'lot':
                    form_names = {'block': 'Bloco', 'slab': 'Placa', 'strip': 'Banda', 'tiles': 'Ladrilhos'}
                    form_name = form_names.get(template.product_form, template.product_form)
                    raise ValidationError(
                        f"❌ Rastreamento por lote obrigatório!\n\n"
                        f"Produtos do tipo '{form_name}' exigem rastreamento por LOTE.\n"
                        f"Por favor, defina 'Rastreamento' como 'Por Lote'."
                    )