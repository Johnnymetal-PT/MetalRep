# -*- coding: utf-8 -*-
from odoo import models, fields, tools, api
from datetime import datetime, date


class StockReservationReport(models.Model):
    _name = 'stock.reservation.report'
    _description = 'Análise de Artigos Reservados'
    _auto = False
    _order = 'date desc, partner_name, product_name'

    # IDs
    id = fields.Integer('ID', readonly=True)
    product_id = fields.Many2one('product.product', 'Produto', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Cliente', readonly=True)
    sale_order_id = fields.Many2one('sale.order', 'Encomenda', readonly=True)
    picking_id = fields.Many2one('stock.picking', 'Picking', readonly=True)
    location_id = fields.Many2one('stock.location', 'Localização', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Armazém', readonly=True)
    lot_id = fields.Many2one('stock.lot', 'Lote', readonly=True)

    # Nomes/Referências
    product_name = fields.Char('Nome Produto', readonly=True)
    product_code = fields.Char('Código Produto', readonly=True)
    partner_name = fields.Char('Nome Cliente', readonly=True)
    sale_order_name = fields.Char('Nº Encomenda', readonly=True)
    location_name = fields.Char('Nome Localização', readonly=True)
    warehouse_name = fields.Char('Nome Armazém', readonly=True)

    # Quantidades
    product_uom_qty = fields.Float('Qtd Solicitada', digits='Product Unit of Measure', readonly=True, aggregator='sum')
    reserved_availability = fields.Float('Qtd Reservada', digits='Product Unit of Measure', readonly=True, aggregator='sum')
    qty_to_reserve = fields.Float('Qtd a Reservar', digits='Product Unit of Measure', readonly=True, aggregator='sum')
    product_uom = fields.Many2one('uom.uom', 'UdM', readonly=True)

    # Dimensões (campos custom do módulo mh_picking)
    length = fields.Float('Comprimento', digits='Dimensions', readonly=True)
    width = fields.Float('Largura', digits='Dimensions', readonly=True)
    thickness = fields.Float('Espessura', digits='Dimensions', readonly=True)
    units_qty = fields.Integer('Unidades', readonly=True, aggregator='sum')

    # Data
    date = fields.Datetime('Data Prevista', readonly=True)
    date_deadline = fields.Date('Data Limite', readonly=True)

    # Estado
    state = fields.Selection([
        ('waiting', 'Aguardando'),
        ('confirmed', 'Confirmado'),
        ('assigned', 'Reservado'),
        ('partially_available', 'Parcialmente Disponível'),
    ], string='Estado', readonly=True)

    reservation_status = fields.Char('Status Reserva', readonly=True)

    # Empresa
    company_id = fields.Many2one('res.company', 'Empresa', readonly=True)

    @api.model
    def get_reservation_data(self, date_from=None, date_to=None, product_form=None, location_id=None):
        """Retorna dados de reservas para o dashboard OWL"""
        # Definir datas padrão
        if not date_from:
            date_from = date.today().replace(day=1).strftime('%Y-%m-%d')
        if not date_to:
            date_to = date.today().strftime('%Y-%m-%d')

        # Construir domínio
        domain = [
            ('date', '>=', date_from),
            ('date', '<=', date_to),
        ]

        if product_form:
            domain.append(('product_id.product_form', '=', product_form))

        if location_id:
            domain.append(('location_id', '=', int(location_id)))

        # Buscar registros
        records = self.search(domain, order='date desc, partner_name, product_name')

        # Formatar dados
        reservations = []
        for rec in records:
            # Corrigir timezone UTC para local (+2h para Moçambique)
            local_date = rec.date
            if rec.date:
                from datetime import timedelta
                local_date = rec.date + timedelta(hours=2)

            reservations.append({
                'id': rec.id,
                'date': local_date.strftime('%Y-%m-%d %H:%M') if local_date else '',
                'product_name': rec.product_id.display_name if rec.product_id else '',
                'partner_name': rec.partner_name or '',
                'sale_order_id': rec.sale_order_id.id if rec.sale_order_id else None,
                'sale_order_name': rec.sale_order_name or '',
                'lot_name': rec.lot_id.name if rec.lot_id else '',
                'reserved_availability': rec.reserved_availability,
                'qty_to_reserve': rec.qty_to_reserve,
                'units_qty': rec.units_qty,
                'length': rec.length,
                'width': rec.width,
                'thickness': rec.thickness,
                'location_name': rec.location_id.complete_name if rec.location_id else '',
                'warehouse_name': rec.warehouse_name or '',
                'reservation_status': rec.reservation_status or '',
                'state': rec.state or '',
                'product_uom': rec.product_uom.name if rec.product_uom else '',
            })

        # Buscar opções de filtro
        locations = self.env['stock.location'].search([('usage', '=', 'internal')], order='complete_name')
        location_options = [{'id': loc.id, 'name': loc.complete_name} for loc in locations]

        return {
            'reservations': reservations,
            'locations': location_options,
            'date_from': date_from,
            'date_to': date_to,
        }

    def init(self):
        """Cria a SQL View para análise de reservas baseada em stock_move_line"""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    -- ID único (usando row_number para garantir unicidade)
                    ROW_NUMBER() OVER (ORDER BY sml.id) AS id,

                    -- Produto
                    sml.product_id AS product_id,
                    pt.name AS product_name,
                    pp.default_code AS product_code,

                    -- Cliente (via sale.order)
                    so.partner_id AS partner_id,
                    rp.name AS partner_name,

                    -- Encomenda
                    so.id AS sale_order_id,
                    so.name AS sale_order_name,

                    -- Picking
                    sml.picking_id AS picking_id,

                    -- Localização
                    sml.location_id AS location_id,
                    sl_src.name AS location_name,
                    sl_src.warehouse_id AS warehouse_id,
                    sw.name AS warehouse_name,

                    -- Lote
                    sml.lot_id AS lot_id,

                    -- Quantidades
                    sm.product_uom_qty AS product_uom_qty,
                    sml.quantity_product_uom AS reserved_availability,
                    (sm.product_uom_qty - COALESCE(sml.quantity_product_uom, 0)) AS qty_to_reserve,
                    sml.product_uom_id AS product_uom,

                    -- Dimensões (campos custom do mh_picking)
                    sml.length AS length,
                    sml.width AS width,
                    sml.thickness AS thickness,
                    sml.units_qty AS units_qty,

                    -- Datas
                    sm.date AS date,
                    sm.date_deadline AS date_deadline,

                    -- Estado
                    sm.state AS state,
                    CASE
                        WHEN sm.state = 'assigned' THEN 'Totalmente Reservado'
                        WHEN sm.state IN ('confirmed', 'waiting') AND sml.quantity_product_uom > 0 THEN 'Parcialmente Reservado'
                        WHEN sm.state IN ('confirmed', 'waiting') THEN 'Aguardando Stock'
                        ELSE 'Outro'
                    END AS reservation_status,

                    -- Empresa
                    sml.company_id AS company_id

                FROM stock_move_line sml
                    INNER JOIN stock_move sm ON sml.move_id = sm.id
                    LEFT JOIN stock_picking sp ON sml.picking_id = sp.id
                    LEFT JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
                    LEFT JOIN product_product pp ON sml.product_id = pp.id
                    LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                    LEFT JOIN sale_order_line sol ON sm.sale_line_id = sol.id
                    LEFT JOIN sale_order so ON sol.order_id = so.id
                    LEFT JOIN res_partner rp ON so.partner_id = rp.id
                    LEFT JOIN stock_location sl_src ON sml.location_id = sl_src.id
                    LEFT JOIN stock_warehouse sw ON sl_src.warehouse_id = sw.id

                WHERE
                    sm.state IN ('assigned', 'confirmed', 'waiting', 'partially_available')
                    AND spt.code = 'outgoing'
                    AND sml.quantity_product_uom > 0
                    AND sm.sale_line_id IS NOT NULL
            )
        """ % self._table)
