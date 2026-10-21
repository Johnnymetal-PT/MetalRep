# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class StockLot(models.Model):
    _inherit = 'stock.lot'

    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        string='Moeda',
        readonly=True,
    )

    # ========================================
    # DIMENSÕES
    # ========================================

    length = fields.Float(
        string='Comprimento',
        digits='Dimensions',
        help='Comprimento específico deste lote em metros',
        readonly=True
    )
    width = fields.Float(
        string='Largura',
        digits='Dimensions',
        help='Largura específica deste lote em metros',
        readonly=True
    )
    thickness = fields.Float(
        string='Espessura',
        digits='Dimensions',
        help='Espessura específica deste lote em metros',
        readonly=True
    )

    # Nome base do lote (sem prefixo sequencial)
    base_lot_name = fields.Char(
        string='Nome Base',
        readonly=True,
        help='Nome base do lote sem prefixo sequencial (ex: "LOTE_ABC" do "#1/MARM001/LOTE_ABC")'
    )

    # ========================================
    # GRUPO DE PREÇOS (mh_picking)
    # ========================================

    price_group_id = fields.Many2one(
        'lot.price.group',
        string='Grupo de Preço',
        readonly=True,
        ondelete='set null',
        help='Grupo que define preço e margem para lotes com dimensões idênticas. '
             'Ao alterar o preço no grupo, todos os lotes associados são atualizados automaticamente.'
    )

    # Campo relacionado para saber se o grupo base usa preço manual
    manual_sale_price = fields.Boolean(
        related='price_group_id.base_manual_sale_price',
        string='Preço Manual (Base)',
        readonly=True,
        help='Indica se o grupo base usa preço de venda manual'
    )

    # ========================================
    # PREÇOS E MARGEM (related do price_group)
    # ========================================

    list_price_lot = fields.Float(
        string='Preço de Venda',
        related='price_group_id.list_price',
        store=True,
        readonly=True,
        digits='Product Price',
        help='Preço de venda herdado do grupo de preço (MT/m² ou MT/m³)'
    )

    margin = fields.Float(
        string='Margem (%)',
        related='price_group_id.margin',
        store=True,
        readonly=True,
        help='Margem de lucro herdada do grupo de preço'
    )

    standard_price = fields.Float(
        string='Custo',
        related='price_group_id.standard_price',
        store=True,
        readonly=True,
        digits='Product Price',
        help='Custo unitário herdado do grupo de preço (MT/m² ou MT/m³)'
    )

    # ========================================
    # PCMP (related do price_group)
    # ========================================

    pcmp = fields.Float(
        string='PCMP',
        related='price_group_id.pcmp',
        store=True,
        readonly=True,
        digits='Product Price',
        help="PCMP herdado do grupo de preço (MT/m² ou MT/m³)"
    )

    uses_pcmp = fields.Boolean(
        string='Usa PCMP',
        compute='_compute_uses_pcmp',
        store=True
    )

    @api.depends('product_id.categ_id.property_cost_method')
    def _compute_uses_pcmp(self):
        for lot in self:
            lot.uses_pcmp = lot.product_id.categ_id.property_cost_method == 'pcmp'

    # Histórico PCMP
    pcmp_history_ids = fields.One2many(
        'stock.lot.pcmp.history',
        'lot_id',
        string='Histórico PCMP'
    )

    # ========================================
    # PESO (mh_picking)
    # ========================================

    peso = fields.Float(
        string='Peso',
        digits=(10, 2),
        compute='_compute_peso',
        store=True,
        readonly=True,
        help='Peso deste lote em kg. Herdado do grupo de preço.'
    )

    @api.depends('price_group_id', 'price_group_id.peso')
    def _compute_peso(self):
        """Herda peso do grupo de preço"""
        for lot in self:
            if lot.sudo().price_group_id and lot.sudo().price_group_id.peso:
                lot.peso = lot.sudo().price_group_id.peso
            else:
                lot.peso = 0.0

    # ========================================
    # CÓDIGO (para barcode/stickers)
    # ========================================

    code = fields.Char(
        string='Código',
        compute='_compute_code',
        store=True,
        readonly=True,
        help='Código extraído do nome do lote (número sequencial). '
             'Ex: "#10/002.333.111/CARRARA_003" → código = "10"'
    )

    @api.depends('name', 'price_group_id')
    def _compute_code(self):
        """Extrai código do nome do lote

        Formato esperado: #N/CÓDIGO/NOME_BASE
        Onde N é o número sequencial que será usado como código.

        Se não tem price_group_id, código = '0'
        """
        for lot in self:
            if lot.sudo().price_group_id and lot.name:
                # Extrair número entre # e primeira /
                # Ex: "#10/002.333.111/CARRARA_003" → "10"
                name = lot.name or ''
                if name.startswith('#'):
                    # Remover # e pegar até a primeira /
                    parts = name[1:].split('/', 1)
                    lot.code = parts[0] if parts else '0'
                else:
                    lot.code = '0'
            else:
                lot.code = '0'

    # ========================================
    # OVERRIDE CREATE (mh_picking)
    # ========================================

    @api.model_create_multi
    def create(self, vals_list):
        """Captura dimensões e base_lot_name do contexto ao criar lote

        Quando um lote é criado durante a validação do picking,
        podemos passar as dimensões e nome base via contexto para preencher
        os campos length, width, thickness, base_lot_name (que são readonly).

        Contexto esperado:
        - lot_length: comprimento do lote
        - lot_width: largura do lote
        - lot_thickness: espessura do lote
        - lot_base_name: nome base do lote
        """
        # Capturar dados do contexto
        length = self.env.context.get('lot_length')
        width = self.env.context.get('lot_width')
        thickness = self.env.context.get('lot_thickness')
        base_lot_name = self.env.context.get('lot_base_name')

        for vals in vals_list:
            # Garantir que company_id está definido
            if not vals.get('company_id'):
                vals['company_id'] = self.env.company.id

            # Só preencher se não foram fornecidas nos vals
            if length and 'length' not in vals:
                vals['length'] = length
            if width and 'width' not in vals:
                vals['width'] = width
            if thickness and 'thickness' not in vals:
                vals['thickness'] = thickness
            if base_lot_name and 'base_lot_name' not in vals:
                vals['base_lot_name'] = base_lot_name

        return super().create(vals_list)


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
