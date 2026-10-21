from odoo import models, fields, api

class BusinessSegment(models.Model):
    _name = 'business.segment'
    _description = 'Segmento de Negócio'
    _order = 'sequence, name'
    _rec_name = 'name'

    name = fields.Char(
        string='Nome do Segmento',
        required=True,
        help='Nome do segmento de negócio'
    )

    code = fields.Char(
        string='Código',
        help='Código único do segmento'
    )

    description = fields.Text(
        string='Descrição',
        help='Descrição detalhada do segmento de negócio'
    )

    active = fields.Boolean(
        string='Ativo',
        default=True,
        help='Se desmarcado, o segmento não aparecerá nas seleções'
    )

    sequence = fields.Integer(
        string='Sequência',
        default=10,
        help='Sequência de exibição'
    )

    color = fields.Integer(
        string='Cor',
        help='Cor para identificação visual'
    )

    product_count = fields.Integer(
        string='Número de Produtos',
        compute='_compute_product_count',
        help='Quantidade de produtos neste segmento'
    )

    @api.depends('name')
    def _compute_product_count(self):
        for segment in self:
            # Contar diretamente product.product já que tem o campo related
            segment.product_count = self.env['product.product'].search_count([
                ('business_segment_id', '=', segment.id)
            ])

    def action_view_products(self):
        """Ação para visualizar produtos (variantes) deste segmento"""
        return {
            'name': f'Produtos - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'view_mode': 'list,form,kanban',
            'domain': [('business_segment_id', '=', self.id)],
            'context': {'default_business_segment_id': self.id}
        }