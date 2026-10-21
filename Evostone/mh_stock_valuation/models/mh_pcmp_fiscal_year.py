# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MhPcmpFiscalYear(models.Model):
    _name = 'mh.pcmp.fiscal.year'
    _inherit = ['mail.thread']
    _description = 'PCMP Ponto de Partida por Ano Fiscal'
    _order = 'fiscal_year desc, product_id'
    _rec_name = 'display_name'

    # Identificação
    product_id = fields.Many2one(
        'product.product',
        string='Produto',
        required=True,
        ondelete='cascade',
        index=True,
    )
    fiscal_year = fields.Integer(
        string='Ano Fiscal',
        required=True,
        index=True,
        default=lambda self: fields.Date.today().year,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        default=lambda self: self.env.company,
        required=True,
    )
    # Grupo de Lote (opcional) - se definido, é o ponto de partida do grupo
    lot_group_id = fields.Many2one(
        'base.lot.group',
        string='Grupo de Lote',
        ondelete='cascade',
        index=True,
        help="Se definido, este é o ponto de partida do grupo de lote. "
             "Se vazio, é o ponto de partida do produto.",
    )

    # Ponto de partida
    initial_stock = fields.Float(
        string='Stock Inicial',
        digits='Product Unit of Measure',
        tracking=True,
        help="Quantidade em stock no início do ano fiscal",
    )
    initial_pcmp = fields.Float(
        string='PCMP Inicial',
        digits='Product Price',
        tracking=True,
        help="Preço de Custo Médio Ponderado no início do ano fiscal",
    )
    initial_value = fields.Float(
        string='Valor Inicial',
        digits='Product Price',
        compute='_compute_initial_value',
        store=True,
        help="Valor total do stock inicial (Stock Inicial × PCMP Inicial)",
    )

    # Campos computados (valores atuais)
    current_pcmp = fields.Float(
        string='PCMP Atual',
        compute='_compute_current_values',
        store=True,
        tracking=True,
        digits='Product Price',
    )
    current_stock = fields.Float(
        string='Stock Atual',
        compute='_compute_current_values',
        store=True,
        tracking=True,
        digits='Product Unit of Measure',
    )
    current_value = fields.Float(
        string='Valor Atual',
        compute='_compute_current_value',
        digits='Product Price',
    )

    # Display
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True,
    )

    _sql_constraints = [
        ('product_year_company_lotgroup_uniq',
         'UNIQUE(product_id, fiscal_year, company_id, lot_group_id)',
         'Já existe um registo PCMP para este produto/grupo neste ano fiscal!'),
    ]

    @api.depends('initial_stock', 'initial_pcmp')
    def _compute_initial_value(self):
        for record in self:
            record.initial_value = record.initial_stock * record.initial_pcmp

    @api.depends('product_id', 'fiscal_year', 'lot_group_id')
    def _compute_display_name(self):
        for record in self:
            if record.product_id and record.fiscal_year:
                if record.lot_group_id:
                    record.display_name = f"{record.lot_group_id.name} - {record.fiscal_year}"
                else:
                    record.display_name = f"{record.product_id.display_name} - {record.fiscal_year}"
            else:
                record.display_name = _("Novo")

    @api.depends('product_id', 'fiscal_year', 'company_id', 'lot_group_id')
    def _compute_current_values(self):
        """Calcula os valores atuais baseado nos movimentos do ano fiscal."""
        for record in self:
            if not record.product_id or not record.fiscal_year:
                record.current_pcmp = 0.0
                record.current_stock = 0.0
                continue

            # Obter PCMP atual (do grupo ou do produto)
            if record.lot_group_id:
                record.current_pcmp = record.lot_group_id.pcmp or record.initial_pcmp
            else:
                record.current_pcmp = record.product_id.pcmp or record.initial_pcmp

            # Calcular stock atual
            date_from = f'{record.fiscal_year}-01-01'
            date_to = f'{record.fiscal_year}-12-31'

            # Entradas do ano
            in_qty = self._get_moves_quantity(record, 'in', date_from, date_to)
            # Saídas do ano
            out_qty = self._get_moves_quantity(record, 'out', date_from, date_to)

            # Stock atual = stock inicial (da transição) + entradas - saídas
            record.current_stock = record.initial_stock + in_qty - out_qty

    @api.depends('current_stock', 'current_pcmp')
    def _compute_current_value(self):
        """Calcula valor atual (non-stored) a partir de stock e pcmp (stored)."""
        for record in self:
            record.current_value = record.current_stock * record.current_pcmp

    def _get_moves_quantity(self, record, move_type, date_from, date_to):
        """Obtém quantidade total de movimentos de entrada ou saída."""
        StockMove = self.env['stock.move']

        domain = [
            ('product_id', '=', record.product_id.id),
            ('state', '=', 'done'),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('company_id', '=', record.company_id.id),
        ]

        # Filtrar por lot_group_id se definido
        if record.lot_group_id:
            domain.append(('lot_group_id', '=', record.lot_group_id.id))
        else:
            domain.append(('lot_group_id', '=', False))

        if move_type == 'in':
            # Movimentos de entrada (location_dest é interna)
            domain.append(('location_dest_id.usage', '=', 'internal'))
            domain.append(('location_id.usage', '!=', 'internal'))
        else:
            # Movimentos de saída (location é interna)
            domain.append(('location_id.usage', '=', 'internal'))
            domain.append(('location_dest_id.usage', '!=', 'internal'))

        moves = StockMove.search(domain)
        return sum(moves.mapped('quantity'))

    @api.constrains('fiscal_year')
    def _check_fiscal_year(self):
        for record in self:
            if record.fiscal_year < 2000 or record.fiscal_year > 2100:
                raise ValidationError(_("O ano fiscal deve estar entre 2000 e 2100."))

    @api.constrains('initial_stock', 'initial_pcmp')
    def _check_positive_values(self):
        for record in self:
            if record.initial_stock <= 0:
                raise ValidationError(_("O stock inicial não pode ser negativo ou não pode ser zero."))
            if record.initial_pcmp <= 0:
                raise ValidationError(_("O PCMP inicial não pode ser negativo ou não pode ser zero.."))

    def action_recalculate_pcmp(self):
        """Ação para forçar recálculo do PCMP do produto ou grupo de lote.

        O PCMP é agora um campo computed. Esta ação invalida o cache
        e força o recálculo.
        """
        self.ensure_one()
        if self.lot_group_id:
            # Forçar recálculo do PCMP do grupo de lote
            self.lot_group_id.invalidate_recordset(['pcmp'])
            self.lot_group_id.modified(['stock_valuation_layer_ids'])
            new_pcmp = self.lot_group_id.pcmp
            target = self.lot_group_id.name
        else:
            # Forçar recálculo do PCMP do produto
            self.product_id.invalidate_recordset(['pcmp'])
            new_pcmp = self.product_id.pcmp
            target = self.product_id.display_name
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('PCMP Recalculado'),
                'message': _('O PCMP de "%s" foi atualizado para: %.2f') % (target, new_pcmp),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
