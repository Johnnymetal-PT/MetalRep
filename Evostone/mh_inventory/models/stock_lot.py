from odoo import api, fields, models


class StockLot(models.Model):
    _inherit = 'stock.lot'

    list_price_lot = fields.Float(
        string='Preço de Venda',
        digits='Product Price',
        compute='_compute_lot_pricing',
        inverse='_inverse_lot_pricing',
        store=True,
        help="Preço de venda específico para este lote."
    )

    margin = fields.Float(
        string='Margem (%)',
        compute='_compute_lot_pricing',
        inverse='_inverse_lot_pricing',
        store=True,
        help="Margem de lucro do lote."
    )

    @api.depends('name', 'product_id', 'product_id.list_price', 'product_id.effective_margin',
                 'standard_price')
    def _compute_lot_pricing(self):
        """Calcula preço e margem do lote"""
        for lot in self:
            # PRIORIDADE 1: Se o lote pertence a um grupo de preço, herdar dele
            if hasattr(lot, 'price_group_id') and lot.sudo().price_group_id:
                lot.list_price_lot = lot.sudo().price_group_id.list_price
                lot.standard_price = lot.sudo().price_group_id.standard_price
                lot.margin = lot.sudo().price_group_id.margin
            # PRIORIDADE 2: Para outros lotes, calcular preço se houver PCMP e margem
            else:
                pcmp = getattr(lot, 'pcmp', 0) or 0
                if pcmp and lot.margin and not lot.list_price_lot:
                    # Preço = PCMP × (1 + Margem/100)
                    lot.list_price_lot = pcmp * (1 + lot.margin / 100)

    def _inverse_lot_pricing(self):
        """Recalcula margem quando preço é alterado manualmente"""
        # Se está vindo de uma propagação do grupo, não fazer inverse para evitar loop
        if self.env.context.get('skip_lot_inverse'):
            return

        for lot in self:
            # Se o lote pertence a um grupo, atualizar o grupo (que propagará para todos os lotes)
            if hasattr(lot, 'price_group_id') and lot.sudo().price_group_id:
                pcmp = getattr(lot, 'pcmp', 0) or 0
                # PRIMEIRO: Recalcular margem se já está definida (antes de propagar)
                if lot.margin > 0:
                    if lot.list_price_lot and pcmp and pcmp > 0:
                        # Margem = [(Preço - PCMP) / PCMP] * 100
                        lot.margin = ((lot.list_price_lot - pcmp) / pcmp) * 100

                # DEPOIS: Propagar valores atualizados para o grupo
                if lot.list_price_lot and pcmp and pcmp > 0:
                    update_vals = {
                        'list_price': lot.list_price_lot,
                        'standard_price': lot.standard_price,
                        'margin': lot.margin,
                    }
                    # Adicionar pcmp se o lote tem esse campo
                    if hasattr(lot, 'pcmp'):
                        update_vals['pcmp'] = lot.pcmp
                    lot.price_group_id.sudo().write(update_vals)              

    @api.onchange('margin')
    def _onchange_margin_cost(self):
        """Atualiza preço ao alterar margem ou PCMP"""
        pcmp = getattr(self, 'pcmp', 0) or 0
        if pcmp and self.margin:
            self.list_price_lot = pcmp * (1 + self.margin / 100)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Atualiza valores quando o produto muda"""
        if self.product_id:
            # Se for novo lote e form do produto != de none, inicializar com valores do produto
            if hasattr(self.product_id, 'product_form') and self.product_id.product_form != 'none':
                if self.list_price_lot:
                    self.list_price_lot = self.product_id.list_price
                    if hasattr(self.product_id, 'effective_margin'):
                        self.margin = self.product_id.effective_margin
                    elif hasattr(self.product_id.product_tmpl_id, 'margin'):
                        self.margin = self.product_id.product_tmpl_id.margin

                # Inicializar custo se não definido
                if not self.standard_price:
                    self.standard_price = self.product_id.standard_price

    @api.model_create_multi
    def create(self, vals_list):
        """Ao criar lote, inicializa com valores apropriados"""
        lots = super().create(vals_list)
        lots._compute_lot_pricing()  # Executa para TODOS de uma vez
        return lots

    def write(self, vals):
        """Garantir que lotes 'SEM-LOTE' sempre herdem do produto"""
        result = super().write(vals)
        if 'name' in vals or 'product_id' in vals:
            self._compute_lot_pricing()
        return result