from odoo import api, fields, models


class StockLotPcmpHistory(models.Model):
    _name = 'stock.lot.pcmp.history'
    _description = 'Histórico de Alterações PCMP'
    _order = 'date desc, id desc'
    _rec_name = 'display_name'


    display_name = fields.Char(
        string='Nome',
        compute='_compute_display_name',
        store=True
    )

    # Referências
    product_id = fields.Many2one(
        'product.product',
        string='Produto',
        required=True,
        ondelete='cascade',
        index=True
    )
    lot_id = fields.Many2one(
        'stock.lot',
        string='Lote/Série',
        domain="[('product_id', '=', product_id)]",
        index=True,
        help='Deixar vazio para produtos sem lote'
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Armazém',
        index=True
    )

    # Valores PCMP
    old_pcmp = fields.Float(
        string='PCMP Anterior',
        digits='Product Price',
        required=True
    )
    new_pcmp = fields.Float(
        string='Novo PCMP',
        digits='Product Price',
        required=True
    )
    difference = fields.Float(
        string='Diferença',
        compute='_compute_difference',
        store=True,
        digits='Product Price'
    )
    difference_percent = fields.Float(
        string='Diferença (%)',
        compute='_compute_difference',
        store=True
    )

    # Contexto da mudança
    date = fields.Datetime(
        string='Data',
        default=fields.Datetime.now,
        required=True,
        index=True
    )
    reason = fields.Selection([
        ('initial', 'Stock Inicial'),
        ('import', 'Importação'),
        ('adjustment', 'Ajuste Manual'),
        ('correction', 'Correção'),
        ('other', 'Outro')
    ], string='Motivo', required=True, default='other')

    origin_document = fields.Char(
        string='Documento Origem',
        help='Documento que originou a mudança (ex: IMP/001, SI/WH1/2024/001)'
    )

    import_document_id = fields.Many2one(
        'import.document',
        string='Doc. Importação',
        ondelete='set null',
        index=True
    )

    stock_initial_id = fields.Many2one(
        'stock.initial',
        string='Stock Inicial',
        ondelete='set null',
        index=True
    )

    # Dados adicionais
    quantity_at_change = fields.Float(
        string='Quantidade no Momento',
        digits='Product Unit of Measure',
        help='Quantidade em stock no momento da mudança'
    )

    notes = fields.Text(string='Observações')

    # Rastreabilidade
    user_id = fields.Many2one(
        'res.users',
        string='Usuário',
        default=lambda self: self.env.user,
        required=True,
        index=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        default=lambda self: self.env.company,
        required=True,
        index=True
    )

    @api.depends('product_id', 'lot_id', 'date', 'new_pcmp')
    def _compute_display_name(self):
        for record in self:
            parts = []
            if record.product_id:
                parts.append(record.product_id.name)
            if record.lot_id:
                parts.append(f'[{record.lot_id.name}]')
            if record.date:
                parts.append(f'- {record.date.strftime("%Y-%m-%d %H:%M")}')
            parts.append(f'→ {record.new_pcmp:.2f}')
            record.display_name = ' '.join(parts)

    @api.depends('old_pcmp', 'new_pcmp')
    def _compute_difference(self):
        for record in self:
            record.difference = record.new_pcmp - record.old_pcmp
            if record.old_pcmp != 0:
                record.difference_percent = (record.difference / record.old_pcmp) * 100
            else:
                record.difference_percent = 0.0

    @api.model
    def create_history(self, product_id, old_pcmp, new_pcmp, reason='other',
                      origin_document=None, lot_id=None, warehouse_id=None,
                      quantity=None, import_document_id=None, stock_initial_id=None,
                      notes=None):
        """
        Método helper para criar histórico PCMP de forma padronizada.

        Args:
            product_id: ID do produto (obrigatório)
            old_pcmp: PCMP anterior
            new_pcmp: Novo PCMP
            reason: Motivo da mudança
            origin_document: Nome do documento origem
            lot_id: ID do lote (opcional)
            warehouse_id: ID do armazém (opcional)
            quantity: Quantidade em stock
            import_document_id: ID do documento de importação (opcional)
            stock_initial_id: ID do stock inicial (opcional)
            notes: Observações adicionais

        Returns:
            stock.lot.pcmp.history: Registo criado
        """
        vals = {
            'product_id': product_id,
            'old_pcmp': old_pcmp,
            'new_pcmp': new_pcmp,
            'reason': reason,
            'origin_document': origin_document,
            'lot_id': lot_id,
            'warehouse_id': warehouse_id,
            'quantity_at_change': quantity,
            'import_document_id': import_document_id,
            'stock_initial_id': stock_initial_id,
            'notes': notes,
        }

        return self.create(vals)