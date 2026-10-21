from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    name = fields.Text(
        string='Description',
        required=False,
    )

    def _get_product_purchase_description(self, product_lang):
        """Não duplicar o nome do produto na coluna Descrição da linha de compra.
        Apenas preenche a descrição se existir uma 'description_purchase' específica no artigo."""
        self.ensure_one()
        if product_lang.description_purchase:
            return product_lang.description_purchase
        return False
    
    @api.constrains('product_qty', 'product_id', 'display_type')
    def _check_quantity_positive(self):
        """Validar que product_qty é maior que zero para linhas de produto.

        Nota: Só valida quando estado != 'draft' para evitar erros durante edição.
        """
        for line in self:
            # Ignorar validação em rascunho - será validado ao confirmar
            if line.order_id.state == 'draft':
                continue

            # Ignorar linhas de seção/nota
            if line.display_type:
                continue

            # Só validar linhas com produto
            if not line.product_id:
                continue
            

            # Validar que product_qty > 0
            if line.product_qty <= 0:
                raise ValidationError(
                    _('❌ Quantidade inválida!\n\n'
                      'Produto: %(product)s\n'
                      'Quantidade: %(qty).2f\n\n'
                      '💡 A quantidade deve ser maior que zero.'
                    ) % {
                        'product': line.product_id.display_name,
                        'qty': line.product_qty,
                    }
                )
                
    def _validate_quantity_positive(self):
        """Validação de quantidade (chamada ao confirmar pedido)"""
        for line in self:
            if line.display_type:
                continue
            if not line.product_id:
                continue
            if line.product_qty <= 0:
                raise ValidationError(
                    _('❌ Quantidade inválida!\n\n'
                      'Produto: %(product)s\n'
                      'Quantidade: %(qty).2f\n\n'
                      '💡 A quantidade deve ser maior que zero.'
                    ) % {
                        'product': line.product_id.display_name,
                        'qty': line.product_qty,
                    }
                )