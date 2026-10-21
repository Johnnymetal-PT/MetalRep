# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StoneStock(models.Model):
    _name = 'stone.stock'
    _description = 'Stock de Pedras (Blocos, Placas, Bandas, Ladrilhos)'
    _order = 'product_id, base_lot_name, code'
    _auto = False  # View SQL - não cria tabela

    # ========================================
    # IDENTIFICAÇÃO
    # ========================================

    product_id = fields.Many2one(
        'product.product',
        string='Produto',
        readonly=True,
    )

    lot_id = fields.Many2one(
        'stock.lot',
        string='Lote (S/N)',
        readonly=True,
    )

    name = fields.Char(
        string='S/N',
        readonly=True,
    )

    description = fields.Char(
        string='Descrição',
        readonly=True,
    )

    base_lot_name = fields.Char(
        string='Nome Base',
        readonly=True,
    )

    code = fields.Char(
        string='Código',
        readonly=True,
    )

    # ========================================
    # ESTADO DO STOCK
    # ========================================

    state = fields.Selection([
        ('available', 'Disponível'),
        ('reserved', 'Reservado'),
        ('no_stock', 'Sem Stock'),
    ], string='Estado', readonly=True)

    # ========================================
    # DIMENSÕES
    # ========================================

    length = fields.Float(
        string='Comprimento',
        digits='Dimensions',
        readonly=True,
    )

    width = fields.Float(
        string='Largura',
        digits='Dimensions',
        readonly=True,
    )

    thickness = fields.Float(
        string='Espessura',
        digits='Dimensions',
        readonly=True,
    )

    area = fields.Float(
        string='Área (m²)',
        digits='Product Unit of Measure',
        readonly=True,
    )

    volume = fields.Float(
        string='Volume (m³)',
        digits='Product Unit of Measure',
        readonly=True,
    )

    # ========================================
    # QUANTIDADES
    # ========================================

    qty_available = fields.Float(
        string='Quantidade Disponível',
        readonly=True,
        digits='Product Unit of Measure',
    )

    qty_reserved = fields.Float(
        string='Quantidade Reservada',
        readonly=True,
        digits='Product Unit of Measure',
    )

    unit_qty = fields.Float(
        string='Quantidade Total',
        readonly=True,
    )

    peso = fields.Float(
        string='Peso (kg)',
        digits=(10, 3),
        readonly=True,
    )

    # ========================================
    # LOCALIZAÇÃO E EMPRESA
    # ========================================

    location_id = fields.Many2one(
        'stock.location',
        string='Localização',
        readonly=True,
    )

    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        readonly=True,
    )

    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        string='Moeda',
        readonly=True,
    )

    # ========================================
    # FORMA DO PRODUTO
    # ========================================

    product_form = fields.Selection([
        ('none', 'Nenhum'),
        ('block', 'Bloco'),
        ('slab', 'Placa'),
        ('strip', 'Banda'),
        ('tiles', 'Ladrilhos'),
    ], string='Forma', readonly=True)

    # ========================================
    # GRUPOS (referência)
    # ========================================

    price_group_id = fields.Many2one(
        'lot.price.group',
        string='Grupo de Dimensões',
        readonly=True,
    )

    base_lot_group_id = fields.Many2one(
        'base.lot.group',
        string='Grupo Base',
        readonly=True,
    )

    # ========================================
    # PREÇOS (informativos)
    # ========================================

    pcmp = fields.Float(
        string='PCMP',
        digits='Product Price',
        readonly=True,
    )

    list_price = fields.Float(
        string='Preço Venda',
        digits='Product Price',
        readonly=True,
    )

    margin = fields.Float(
        string='Margem (%)',
        readonly=True,
    )

    # ========================================
    # ACÇÕES
    # ========================================

    def action_open_traceability(self):
        """Abre o Relatório de Rastreamento do lot da pedra."""
        self.ensure_one()
        if not self.lot_id:
            return False
        action = self.env['ir.actions.actions']._for_xml_id('stock.action_stock_report')
        action['context'] = {
            'active_id': self.lot_id.id,
            'active_model': 'stock.lot',
        }
        return action

    def action_open_stone_pricelist_report(self):
        """Abre o relatório interactivo de Lista de Preços de Pedras.

        Identifica os lot.price.group distintos das pedras seleccionadas
        e abre o componente client-side para preview/print.
        """
        price_group_ids = self.mapped('price_group_id').ids
        if not price_group_ids:
            from odoo.exceptions import UserError
            raise UserError(_("Nenhuma das pedras seleccionadas tem Grupo de Preço definido."))
        return {
            'type': 'ir.actions.client',
            'tag': 'generate_stone_pricelist_report',
            'name': _('Lista de Preços'),
            'context': {
                'active_ids': self.ids,
                'active_model': 'stone.stock',
                'price_group_ids': price_group_ids,
                'default_price_group_id': price_group_ids[0],
            },
        }

    # ========================================
    # SQL VIEW
    # ========================================

    def init(self):
        """Cria a view SQL para stone.stock"""
        self.env.cr.execute("""
            DROP VIEW IF EXISTS stone_stock;
            CREATE OR REPLACE VIEW stone_stock AS (
                SELECT
                    -- ID único (combinação de lot + location)
                    ROW_NUMBER() OVER () as id,

                    -- Identificação
                    sl.product_id,
                    sl.id as lot_id,
                    COALESCE(sl.name, '') as name,
                    COALESCE(lpg.description, '') as description,
                    COALESCE(sl.base_lot_name, '') as base_lot_name,
                    COALESCE(sl.code, '0') as code,

                    -- Estado baseado em quantidades
                    CASE
                        WHEN COALESCE(sq.quantity, 0) - COALESCE(sq.reserved_quantity, 0) > 0 THEN 'available'
                        WHEN COALESCE(sq.reserved_quantity, 0) > 0 THEN 'reserved'
                        ELSE 'no_stock'
                    END as state,

                    -- Dimensões do lote
                    COALESCE(sl.length, 0) as length,
                    COALESCE(sl.width, 0) as width,
                    COALESCE(sl.thickness, 0) as thickness,

                    -- Área e Volume do grupo de dimensões
                    COALESCE(lpg.area, 0) as area,
                    COALESCE(lpg.volume, 0) as volume,

                    -- Quantidades
                    COALESCE(sq.quantity, 0) - COALESCE(sq.reserved_quantity, 0) as qty_available,
                    COALESCE(sq.reserved_quantity, 0) as qty_reserved,
                    COALESCE(sq.quantity, 0) as unit_qty,

                    -- Peso
                    COALESCE(sl.peso, 0) as peso,

                    -- Localização e Empresa
                    sq.location_id,
                    sl.company_id,

                    -- Forma do produto
                    COALESCE(pt.product_form, 'none') as product_form,

                    -- Grupos
                    sl.price_group_id,
                    lpg.base_lot_group_id,

                    -- Preços do grupo de dimensões
                    COALESCE(lpg.pcmp, 0) as pcmp,
                    COALESCE(lpg.list_price, 0) as list_price,
                    COALESCE(lpg.margin, 0) as margin

                FROM stock_lot sl

                -- Join com quants para quantidades
                LEFT JOIN stock_quant sq ON sq.lot_id = sl.id

                -- Join com grupo de dimensões
                LEFT JOIN lot_price_group lpg ON lpg.id = sl.price_group_id

                -- Join com produto para forma
                LEFT JOIN product_product pp ON pp.id = sl.product_id
                LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id

                -- Filtrar apenas localizações internas (armazém)
                LEFT JOIN stock_location loc ON loc.id = sq.location_id

                WHERE loc.usage = 'internal' OR loc.id IS NULL

                ORDER BY sl.product_id, sl.base_lot_name, sl.code
            )
        """)
