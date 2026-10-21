from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class StockLot(models.Model):
    _inherit = 'stock.lot'

    # Campo PCMP computado - herda do price_group_id se existir
    pcmp = fields.Float(
        string='PCMP',
        compute='_compute_pcmp',
        store=True,
        readonly=True,
        digits='Product Price',
        help="PCMP herdado do grupo de preço (se existir)",
        copy=False
    )

    @api.depends('price_group_id', 'price_group_id.pcmp')
    def _compute_pcmp(self):
        """Herda PCMP do grupo de preço, ou 0 se não tiver grupo"""
        for lot in self:
            if lot.sudo().price_group_id and lot.sudo().price_group_id.pcmp:
                lot.pcmp = lot.sudo().price_group_id.pcmp
            else:
                lot.pcmp = 0.0

    uses_pcmp = fields.Boolean(
        string='Usa PCMP',
        compute='_compute_uses_pcmp',
        store=True
    )

    @api.depends('product_id.categ_id.property_cost_method')
    def _compute_uses_pcmp(self):
        for lot in self:
            lot.uses_pcmp = lot.product_id.categ_id.property_cost_method == 'pcmp'

    currency_id = fields.Many2one(
        'res.currency',
        string='Moeda',
        related='company_id.currency_id',
        readonly=True
    )

    # Histórico PCMP
    pcmp_history_ids = fields.One2many(
        'stock.lot.pcmp.history',
        'lot_id',
        string='Histórico PCMP'
    )




class StockLotPcmpHistory(models.Model):
    _name = 'stock.lot.pcmp.history'
    _description = 'Histórico PCMP do Lote'
    _order = 'date desc'
    _rec_name = 'date'

    lot_id = fields.Many2one(
        'stock.lot',
        string='Lote',
        required=True,
        ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.product',
        string='Produto',
        help='Produto associado ao lote'
    )
    date = fields.Datetime(
        string='Data',
        required=True,
        default=fields.Datetime.now
    )
    old_pcmp = fields.Float(
        string='PCMP Anterior',
        digits='Product Price'
    )
    new_pcmp = fields.Float(
        string='PCMP Novo',
        digits='Product Price'
    )
    origin = fields.Char(
        string='Origem',
        help='Documento que originou a mudança'
    )
    origin_document = fields.Char(
        string='Documento Origem',
        help='Referência do documento que originou a mudança'
    )
    user_id = fields.Many2one(
        'res.users',
        string='Utilizador',
        required=True
    )
    quantity_at_change = fields.Float(
        string='Quantidade',
        digits='Product Unit of Measure',
        help='Quantidade em stock no momento da alteração'
    )
    notes = fields.Text(string='Notas')