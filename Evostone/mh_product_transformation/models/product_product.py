from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProductProduct(models.Model):
    _inherit = 'product.product'

    can_be_transformed = fields.Boolean(
        string='Pode ser Transformado',
        related='product_tmpl_id.can_be_transformed',
        store=True,
        readonly=False,
        help='Indica se este produto pode ser transformado'
    )

    product_form = fields.Selection(
        string='Forma do Produto',
        related='product_tmpl_id.product_form',
        store=True,
        readonly=False,
        help='Define a forma do produto: Bloco pode virar Placa, Placa pode virar Banda')

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

    @api.onchange('product_tmpl_id')
    def _onchange_product_tmpl_id(self):
        """Sincroniza campos quando o template muda"""
        if self.use_variant_price:
            # Manter valores independentes quando use_variant_price = True
            self.can_be_transformed = self.product_tmpl_id.can_be_transformed
            self.product_form = self.product_tmpl_id.product_form
            # return
        else:
            # Herdar do template
            self.can_be_transformed = self.product_tmpl_id.can_be_transformed
            self.product_form = self.product_tmpl_id.product_form

    @api.constrains('product_form', 'uom_id')
    def _check_uom_compatibility(self):
        """Valida se a unidade de medida é compatível com a forma do produto"""
        uom_cubic = self.env.ref('uom.product_uom_cubic_meter', raise_if_not_found=False)
        uom_square = self.env.ref('uom.uom_square_meter', raise_if_not_found=False)

        for product in self:
            if product.product_form == 'block' and product.uom_id != uom_cubic:
                raise ValidationError(
                    "Produtos do tipo 'Bloco' só podem usar a unidade de medida m³ (metro cúbico)."
                )
            elif product.product_form in ['slab', 'strip', 'tiles'] and product.uom_id != uom_square:
                form_names = {'slab': 'Placa', 'strip': 'Banda', 'tiles': 'Ladrilhos'}
                form_name = form_names.get(product.product_form, product.product_form)
                raise ValidationError(
                    f"Produtos do tipo '{form_name}' só podem usar a unidade de medida m² (metro quadrado)."
                )

    @api.constrains('product_form', 'is_storable', 'tracking')
    def _check_tracking_required(self):
        """Valida que produtos com forma específica são estocáveis com rastreamento por lote"""
        for product in self:
            if product.product_form != 'none':
                if not product.is_storable:
                    form_names = {'block': 'Bloco', 'slab': 'Placa', 'strip': 'Banda', 'tiles': 'Ladrilhos'}
                    form_name = form_names.get(product.product_form, product.product_form)
                    raise ValidationError(
                        f"❌ Produto deve ser estocável!\n\n"
                        f"Produtos do tipo '{form_name}' devem ser produtos estocáveis.\n"
                        f"Por favor, marque 'Pode ser estocado'."
                    )

                if product.tracking != 'lot':
                    form_names = {'block': 'Bloco', 'slab': 'Placa', 'strip': 'Banda', 'tiles': 'Ladrilhos'}
                    form_name = form_names.get(product.product_form, product.product_form)
                    raise ValidationError(
                        f"❌ Rastreamento por lote obrigatório!\n\n"
                        f"Produtos do tipo '{form_name}' exigem rastreamento por LOTE.\n"
                        f"Por favor, defina 'Rastreamento' como 'Por Lote'."
                    )
