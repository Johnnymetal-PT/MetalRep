from odoo import api, fields, models, _
from odoo.exceptions import UserError

# Códigos de área que representam produtos físicos (com stock)
PRODUCT_AREA_CODES = {'raw_material', 'auxiliary_material', 'packaging_material', 'fixed_asset', 'finished_product', 'merchandise', 'other'}
# Códigos de área de produtos físicos (sem 'other') - para validações de peso e artigos armazenáveis
PHYSICAL_PRODUCT_CODES = {'raw_material', 'auxiliary_material', 'packaging_material', 'fixed_asset', 'finished_product', 'merchandise'}


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    service_type_id = fields.Many2one(
        'service.type',
        string='Tipo de Serviço',
        required=True,
        tracking=True,
        help='Tipo de serviço específico desta ordem de compra'
    )

    service_type_area_ids = fields.Many2many(
        'service.type.area',
        'purchase_order_service_type_area_rel',
        'order_id',
        'area_id',
        string='Áreas de Actuação',
        compute='_compute_service_type_fields',
        store=True,
        readonly=True,
    )

    is_product_type = fields.Boolean(
        string='Tipo Produto',
        compute='_compute_service_type_fields',
        store=True,
        help='Indica se a PO é de produto (matéria prima, material auxiliar, etc.) vs serviço'
    )

    service_type_color = fields.Selection([
        ('primary', 'Azul'),
        ('info', 'Azul Claro'),
        ('success', 'Verde'),
        ('warning', 'Amarelo'),
        ('danger', 'Vermelho'),
        ('muted', 'Cinzento'),
    ], string='Cor Tipo Serviço',
       compute='_compute_service_type_fields',
       store=True,
    )

    is_import_related = fields.Boolean(
        string='Relacionado com Importação',
        help='Indica se esta PO está relacionada com algum documento de importação'
    )

    @api.depends('service_type_id')
    def _compute_service_type_fields(self):
        """Copiar áreas, cor e is_product_type do tipo de serviço (snapshot)."""
        for order in self:
            if order.service_type_id:
                order.service_type_area_ids = order.service_type_id.area_ids
                order.service_type_color = order.service_type_id.color
                area_codes = set(order.service_type_id.area_ids.mapped('code'))
                order.is_product_type = bool(area_codes & PRODUCT_AREA_CODES)
            else:
                order.service_type_area_ids = False
                order.service_type_color = False
                order.is_product_type = False

    def _get_area_codes(self):
        """Retorna set dos códigos das áreas de actuação da PO (snapshot)"""
        self.ensure_one()
        return set(self.service_type_area_ids.mapped('code'))

    # def action_create_invoice(self):
    #     """Bloquear criação de fatura se picking não validado ou quantidades não recebidas.
    #     POs de serviço (sem pickings) não são validadas."""
    #     for order in self:
    #         # Só validar se a PO tiver pickings associados
    #         if not order.picking_ids:
    #             continue

    #         # Verificar effective_date
    #         if not order.effective_date:
    #             raise UserError(_(
    #                 'Não é possível criar fatura para a PO "%s".\n\n'
    #                 'Recepcione os artigos para depois criar a fatura.',
    #                 order.name,
    #             ))

    #         # Verificar pickings todos validados (ignorar cancelados)
    #         not_done = order.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel'))
    #         if not_done:
    #             raise UserError(_(
    #                 'Não é possível criar fatura para a PO "%s".\n\n'
    #                 'Recepcione os artigos para depois criar a fatura.',
    #                 order.name,
    #             ))

    #         # Verificar qty_received em todas as linhas de produto
    #         lines_not_received = order.order_line.filtered(
    #             lambda l: l.product_id and l.product_id.type != 'service' and l.qty_received <= 0
    #         )
    #         if lines_not_received:
    #             raise UserError(_(
    #                 'Não é possível criar fatura para a PO "%s".\n\n'
    #                 'Recepcione os artigos para depois criar a fatura.',
    #                 order.name,
    #             ))

    #     return super().action_create_invoice()

