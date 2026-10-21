from odoo import models, fields, api

class ProductFamily(models.Model):
    _name = 'product.family'
    _description = 'Família de Produtos'
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char(
        string='Nome da Família',
        required=True,
        help='Nome da família de produtos'
    )

    code = fields.Char(
        string='Código',
        help='Código único da família'
    )

    description = fields.Text(
        string='Descrição',
        help='Descrição detalhada da família de produtos'
    )

    active = fields.Boolean(
        string='Ativo',
        default=True,
        help='Se desmarcado, a família não aparecerá nas seleções'
    )

    product_count = fields.Integer(
        string='Número de Produtos',
        compute='_compute_product_count',
        help='Quantidade de produtos nesta família'
    )

    @api.depends('name')
    def _compute_product_count(self):
        for family in self:
            # Contar diretamente product.product já que tem o campo related
            family.product_count = self.env['product.product'].search_count([
                ('product_family_id', '=', family.id)
            ])

    def action_view_products(self):
        """Ação para visualizar produtos (variantes) desta família"""
        return {
            'name': f'Produtos - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'view_mode': 'list,form,kanban',
            'domain': [('product_family_id', '=', self.id)],
            'context': {'default_product_family_id': self.id}
        }
