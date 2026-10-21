from odoo import models, fields, api
import math

class ProductAttributeValue(models.Model):
    _inherit = "product.template.attribute.value"

    preco_por_m2 = fields.Float(string="Preço por m²")
    m2_da_peca = fields.Float(string="m² da Peça / Metragem")
    #metragem_yards = fields.Float(string="Metragens (yards)")
    valor_do_corte = fields.Float(string="Valor do Corte")
    margem = fields.Float(string="Margem")
    margem_geral = fields.Float(string="Margem Geral")

    price_extra = fields.Float(
        string="Value Price Extra",
        compute="_compute_price_extra",
        store=True
    )

    @api.depends('preco_por_m2', 'm2_da_peca', 'valor_do_corte', 'margem', 'margem_geral')
    def _compute_price_extra(self):
        """ Compute price_extra using multiplication, treating zero values as 1, but if all are 0, result is 0 """
        for record in self:
            # Check if all values are 0
            if all(value == 0 for value in [
                record.preco_por_m2,
                record.m2_da_peca,
                record.valor_do_corte,
                record.margem,
                record.margem_geral
            ]):
                record.price_extra = 0
            else:
                # Apply failsafe logic (treat 0 as 1)
                preco_por_m2 = record.preco_por_m2 if record.preco_por_m2 > 0 else 1
                m2_da_peca = record.m2_da_peca if record.m2_da_peca > 0 else 1
                valor_do_corte = record.valor_do_corte
                margem = record.margem if record.margem > 0 else 1
                margem_geral = record.margem_geral if record.margem_geral > 0 else 1

                # Compute price_extra
                record.price_extra = preco_por_m2 * m2_da_peca * margem * margem_geral + valor_do_corte 
                
class ProductTemplate(models.Model):
    _inherit = "product.template"

    x_studio_margem = fields.Float(string="Margem")  # First Margem
    x_studio_margem_2_2 = fields.Float(string="Margem Extra")  # Second Margem
    x_studio_valor_interno = fields.Float(
        string="Valor Interno",
        compute="_compute_internal_value",
        store=True
    )
    list_price = fields.Float(
        string="Sales Price",
        compute="_compute_list_price",
        store=True
    )

    @api.depends('seller_ids.price', 'x_studio_margem', 'x_studio_margem_2_2')
    def _compute_list_price(self):
        """ Compute list_price using total supplier prices * both margem fields, rounded up """
        for product in self:
            supplier_price = sum(product.seller_ids.mapped('price')) or 1
            margem_1 = max(product.x_studio_margem, 1)
            margem_2 = max(product.x_studio_margem_2_2, 1)
            product.list_price = math.ceil(supplier_price * margem_1 * margem_2)

    @api.depends('seller_ids.price', 'x_studio_margem')
    def _compute_internal_value(self):
        """ Compute x_studio_valor_interno using total supplier prices * first margem, rounded up """
        for product in self:
            supplier_price = sum(product.seller_ids.mapped('price')) or 1
            margem_1 = max(product.x_studio_margem, 1)
            product.x_studio_valor_interno = math.ceil(supplier_price * margem_1)
