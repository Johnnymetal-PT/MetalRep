from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    scrap_id = fields.Many2one(
        'stock.scrap',
        string='Descarte Origem',
        readonly=True,
        copy=False,
    )

    is_picking_readonly = fields.Boolean(
        string='Picking em Modo Somente Leitura',
        compute='_compute_is_picking_readonly',
        help='Indica se o picking deve ser somente leitura (verdadeiro quando vem de venda)'
    )

    # Campos de cubicagem
    total_area = fields.Float(
        string='Área Total (m²)',
        compute='_compute_cubage',
        store=True,
        digits=(16, 3),
        help='Soma das áreas de todas as linhas'
    )

    total_volume = fields.Float(
        string='Volume Total (m³)',
        compute='_compute_cubage',
        store=True,
        digits=(16, 3),
        help='Soma dos volumes de todas as linhas'
    )

    total_weight = fields.Float(
        string='Peso Total (KG)',
        compute='_compute_cubage',
        store=True,
        digits=(16, 2),
        help='Peso total de todos os produtos'
    )

    @api.depends('move_line_ids.quantity',
                 'move_line_ids.product_id.product_form',
                 'move_line_ids.peso')
    def _compute_cubage(self):
        """Soma área, volume e peso a partir das move_lines.

        - block: quantity = m³ → soma directa em total_volume
        - slab/strip/tiles: quantity = m² → soma directa em total_area
        - peso: já é compute store na move_line (com cascata e snapshot por
          state guard a nível da move_line). Header só soma.
        """
        for picking in self:
            total_area = 0.0
            total_volume = 0.0
            total_weight = 0.0
            for line in picking.move_line_ids:
                if not line.product_id:
                    continue
                product_form = getattr(line.product_id, 'product_form', 'none')
                qty = line.quantity or 0.0
                if product_form == 'block':
                    total_volume += qty
                elif product_form in ('slab', 'strip', 'tiles'):
                    total_area += qty
                total_weight += line.peso or 0.0
            picking.total_area = total_area
            picking.total_volume = total_volume
            picking.total_weight = total_weight

    def _check_duplicate_lot_groups(self):
        """Override para permitir reutilizar base_lot_name em pickings de scrap

        Quando um scrap de remediação/transformação gera um picking de entrada,
        o base_lot_name é o mesmo do lote original (intencionalmente).
        Salta verificação se contexto 'from_scrap' ou se picking tem scrap_id.

        Também salta se contexto 'bypass_duplicate_lot_check' está activo —
        usado em correcções pontuais (ex: adicionar placas esquecidas a um
        base.lot.group existente sem ter de reabrir o IMP fechado).
        """
        if (self.env.context.get('from_scrap')
                or self.env.context.get('bypass_duplicate_lot_check')
                or self.scrap_id):
            return
        return super()._check_duplicate_lot_groups()

    @api.depends('sale_id', 'transformation_id')
    def _compute_is_picking_readonly(self):
        """Determina se o picking deve ser readonly

        O picking é readonly quando:
        - Está vinculado a uma ordem de venda (sale_id), ou
        - Está vinculado a um documento de transformação (transformation_id):
          nesse caso o utilizador só edita pelas linhas do documento
          (input/output), nunca pelo picking. A sincronização é só forward
          (documento -> picking), sem risco de exigir sincronização reversa.
        """
        for record in self:
            record.is_picking_readonly = bool(record.sale_id) or bool(record.transformation_id)

    def _can_return(self):
        """Backport do fix da saas-19.2.

        Override do `sale_stock._can_return` que retorna `super() or self.sale_id`
        — quando o picking tem sale_id, retorna o recordset (truthy) em vez de False,
        permitindo criar devoluções de pickings ainda em estado `assigned`/`confirmed`.

        Restaura a regra correcta: só pickings em `done` podem ser devolvidos.
        """
        self.ensure_one()
        return self.state == 'done'
