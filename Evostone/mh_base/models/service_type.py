from odoo import api, fields, models


class ServiceTypeArea(models.Model):
    _name = 'service.type.area'
    _description = 'Área de Actuação'
    _order = 'sequence, name'

    name = fields.Char(string='Nome', required=True)
    code = fields.Selection([
        ('raw_material', 'Matéria Prima'),
        ('auxiliary_material', 'Material Auxiliar'),
        ('packaging_material', 'Material Embalagem'),
        ('fixed_asset', 'Imobilizado/Consumivel'),
        ('finished_product', 'Produto Acabado'),
        ('merchandise', 'Mercadoria'),
        ('purchase_service', 'Serviço de Compra'),
        ('service', 'Serviço'),
        ('other', 'Outros'),
    ], string='Código', required=True)
    sequence = fields.Integer(string='Sequência', default=10)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'O código da área de actuação deve ser único!')
    ]


class ServiceType(models.Model):
    _name = 'service.type'
    _description = 'Tipo de Serviço'
    _order = 'sequence, name'

    name = fields.Char(string='Nome', required=True)
    sequence = fields.Integer(string='Sequência', default=10)
    active = fields.Boolean(string='Activo', default=True)

    area_ids = fields.Many2many(
        'service.type.area',
        string='Áreas de Actuação',
        required=True,
        help='Classificação das áreas de actuação deste tipo de serviço',
    )

    color = fields.Selection([
        ('primary', 'Azul'),
        ('info', 'Azul Claro'),
        ('success', 'Verde'),
        ('warning', 'Amarelo'),
        ('danger', 'Vermelho'),
        ('muted', 'Cinzento'),
    ], string='Cor', default='primary')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'O nome do tipo de serviço deve ser único!')
    ]
