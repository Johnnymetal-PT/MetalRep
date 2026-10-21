from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    # Sobrescrever campos para remover obrigatoriedade
    # Permite preencher via wizard de seleção de stock
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=False,
        check_company=True,
        domain="[('type', '=', 'consu')]",
        readonly=False
    )

    lot_id = fields.Many2one(
        'stock.lot',
        string='Lot/Serial Number',
        required=False,
        check_company=True,
        domain="[('product_id', '=', product_id)]",
        readonly=False
    )

    product_uom_id = fields.Many2one(
        'uom.uom', 'Unit of Measure',
        compute="_compute_product_uom_id", store=True, readonly=True, precompute=True,
        required=False, domain="[('category_id', '=', product_uom_category_id)]")

    selected_quant_id = fields.Many2one(
        'stock.quant',
        string='Stock Selecionado',
        help='Quant selecionado via wizard de seleção de stock'
    )

    product_form = fields.Selection(
        related='product_id.product_form',
        string='Forma do Produto',
        readonly=True,
        store=False
    )

    # ========================================
    # TIPO DE SCRAP
    # ========================================

    scrap_type = fields.Selection([
        ('break', 'Quebra'),
        ('remediation', 'Remediação'),
    ], string='Tipo de Descarte', default='break', required=True,
        help='Quebra: descarte total (conta 6842). Sobras opcionais (conta 7642).\n'
             'Remediação: re-medição (conta 6849). Novas placas obrigatórias (conta 7649).')

    # Linhas de saída (sobras para quebra, novas placas para remediação)
    scrap_line_ids = fields.One2many(
        'stock.scrap.transformation.line',
        'scrap_id',
        string='Peças de Saída',
    )

    has_leftover = fields.Boolean(
        string='Tem Sobras?',
        default=False,
        help='Marque se da quebra resultaram pedaços aproveitáveis.',
    )

    is_reserved = fields.Boolean(
        string='Stock Reservado',
        default=False,
        readonly=True,
        copy=False,
    )

    # Picking de entrada gerado (referência)
    entry_picking_id = fields.Many2one(
        'stock.picking',
        string='Picking de Entrada',
        readonly=True,
        help='Picking de recepção gerado pela quebra (sobras) ou remediação',
    )

    @api.onchange('location_id')
    def _onchange_location_id(self):
        """Limpar dados do produto selecionado quando location_id mudar"""
        self.product_id = False
        self.lot_id = False
        self.product_uom_id = False
        self.scrap_qty = 0.0
        self.selected_quant_id = False
        self.quant_location_id = False
        self.quant_on_hand = 0.0
        self.quant_available = 0.0
        self.quant_length = 0.0
        self.quant_width = 0.0
        self.quant_thickness = 0.0
        self.quant_units = 0
        self.has_leftover = False
        self.scrap_line_ids = [(5, 0, 0)]

    @api.onchange('has_leftover')
    def _onchange_has_leftover(self):
        """Limpar linhas de sobras ao desmarcar o toggle"""
        if not self.has_leftover:
            self.scrap_line_ids = [(5, 0, 0)]

    @api.onchange('product_id')
    def _onchange_product_id_scrap_type(self):
        """Forçar tipo 'quebra' para produtos sem forma física e limpar dados"""
        self.scrap_line_ids = [(5, 0, 0)]
        self.has_leftover = False
        if self.product_form == 'none':
            self.scrap_type = 'break'

    @api.onchange('scrap_type')
    def _onchange_scrap_type(self):
        """Limpar linhas, toggle e seleccionar localização de scrap ao mudar tipo"""
        self.scrap_line_ids = [(5, 0, 0)]
        self.has_leftover = False
        remediation_loc = self.env.ref('mh_picking.stock_location_remediacoes', raise_if_not_found=False)
        if self.scrap_type == 'remediation' and remediation_loc:
            self.scrap_location_id = remediation_loc.id
        elif self.scrap_type == 'break':
            scrap_loc = self.env['stock.location'].search([
                ('scrap_location', '=', True),
                ('company_id', 'in', [self.company_id.id, False]),
                ('id', '!=', remediation_loc.id if remediation_loc else 0),
            ], limit=1)
            if scrap_loc:
                self.scrap_location_id = scrap_loc.id

    # Campos para armazenar detalhes do quant no momento da seleção
    quant_location_id = fields.Many2one(
        'stock.location',
        string='Localização do Quant',
        readonly=True,
        store=True
    )

    quant_on_hand = fields.Float(
        string='Volume/Área/Unidade Em Mão',
        readonly=True,
        store=True,
        digits='Product Unit of Measure',
    )

    quant_available = fields.Float(
        string='Volume/Área/Unidade Disponível',
        readonly=True,
        store=True,
        digits='Product Unit of Measure',
    )

    quant_length = fields.Float(
        string='Comprimento',
        readonly=True,
        store=True,
        digits='Dimensions',
    )

    quant_width = fields.Float(
        string='Largura',
        readonly=True,
        store=True,
        digits='Dimensions',
    )

    quant_thickness = fields.Float(
        string='Espessura',
        readonly=True,
        store=True,
        digits='Dimensions',
    )

    quant_units = fields.Integer(
        string='Quantidade',
        readonly=True,
        store=True
    )

    def _prepare_move_values(self):
        """Override para incluir dimensões do quant selecionado no move e move_line"""
        vals = super()._prepare_move_values()

        if self.selected_quant_id:
            vals.update({
                'length': self.quant_length,
                'width': self.quant_width,
                'thickness': self.quant_thickness,
                'units_qty': self.quant_units or 1,
            })

            if vals.get('move_line_ids') and vals['move_line_ids']:
                move_line_vals = vals['move_line_ids'][0][2]
                move_line_vals.update({
                    'length': self.quant_length,
                    'width': self.quant_width,
                    'thickness': self.quant_thickness,
                    'units_qty': self.quant_units or 1,
                })

        return vals

    def action_open_entry_picking(self):
        """Abrir o picking de entrada associado"""
        self.ensure_one()
        if not self.entry_picking_id:
            return
        return {
            'type': 'ir.actions.act_window',
            'name': _('Picking de Entrada'),
            'res_model': 'stock.picking',
            'res_id': self.entry_picking_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_select_stock_wizard(self):
        """Abrir wizard de seleção de stock"""
        self.ensure_one()

        if not self.location_id:
            raise UserError(_('Por favor, selecione uma localização primeiro.'))
        if self.is_reserved:
            raise UserError(_('Não é possível alterar o stock enquanto a reserva estiver activa. Liberte a reserva primeiro.'))

        wizard = self.env['stock.scrap.select.wizard'].create({
            'scrap_id': self.id,
            'location_id': self.location_id.id,
        })

        wizard._load_available_stock()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Selecionar Stock para Descarte'),
            'res_model': 'stock.scrap.select.wizard.line',
            'view_mode': 'list,form',
            'views': [(False, 'list'), (False, 'form')],
            'domain': [('wizard_id', '=', wizard.id)],
            'context': {
                'search_default_available': 1,
                'default_wizard_id': wizard.id,
            },
            'target': 'new',
        }

    # ========================================
    # RESERVA DE STOCK
    # ========================================

    def action_reserve_stock(self):
        """Reservar stock criando um stock.move com lot_id do scrap"""
        self.ensure_one()
        if not self.product_id or not self.scrap_qty:
            raise UserError(_('Selecione um artigo e quantidade antes de reservar.'))
        if self.is_reserved:
            raise UserError(_('O stock já está reservado.'))

        move_vals = self._prepare_move_values()
        move_vals.pop('move_line_ids', None)
        move_vals.pop('picked', None)
        move_vals['state'] = 'draft'
        # Forçar reserva do lote correcto via stock_restrict_lot
        if self.lot_id:
            move_vals['restrict_lot_id'] = self.lot_id.id

        move = self.env['stock.move'].create(move_vals)
        move._action_confirm()
        move._action_assign()

        if move.state == 'assigned':
            self.is_reserved = True
            _logger.info('Scrap %s: stock reservado (move %s)', self.name, move.id)
        else:
            move._action_cancel()
            move.unlink()
            raise UserError(_(
                'Não foi possível reservar o stock. Verifique a disponibilidade.'
            ))

    def action_unreserve_stock(self):
        """Libertar a reserva de stock cancelando o move"""
        self.ensure_one()
        if not self.is_reserved:
            return

        # Guardar scrap_qty antes de apagar moves (scrap_qty é computed de move_ids)
        original_qty = self.scrap_qty

        reserve_moves = self.move_ids.filtered(lambda m: m.state in ('confirmed', 'assigned'))
        if reserve_moves:
            reserve_moves._action_cancel()
            reserve_moves.unlink()

        # Restaurar scrap_qty (o compute resetou para 1.0)
        self.scrap_qty = original_qty
        self.is_reserved = False
        _logger.info('Scrap %s: reserva libertada', self.name)

    def do_scrap(self):
        """Override para usar move reservado se existir"""
        self._check_company()
        for scrap in self:
            reserved_move = scrap.move_ids.filtered(lambda m: m.state == 'assigned')
            if reserved_move:
                scrap.name = self.env['ir.sequence'].next_by_code('stock.scrap') or _('New')
                # Atualizar origin e reference no move (foram criados quando name era "Novo")
                reserved_move.write({
                    'origin': scrap.origin or scrap.picking_id.name or scrap.name,
                    'name': scrap.name,
                    'reference': scrap.name,
                })
                # Preencher quantity na move_line e marcar picked
                for ml in reserved_move.move_line_ids:
                    ml.quantity = scrap.scrap_qty
                reserved_move.picked = True
                reserved_move.with_context(is_scrap=True)._action_done()
                scrap.write({'state': 'done'})
                scrap.date_done = fields.Datetime.now()
                if scrap.should_replenish:
                    scrap.do_replenish()
            else:
                return super(StockScrap, scrap).do_scrap()
        return True

    # ========================================
    # VALIDAÇÃO
    # ========================================

    def action_validate(self):
        """Override para tratar sobras (quebra) e novas placas (remediação)"""
        self.ensure_one()

        # Produtos sem forma: só quebra permitida
        if self.product_form == 'none' and self.scrap_type != 'break':
            raise UserError(_(
                'Produtos sem forma física só permitem descarte do tipo Quebra.'
            ))

        # Remediação: obrigatório ter pelo menos 1 linha
        if self.scrap_type == 'remediation':
            if not self.scrap_line_ids:
                raise UserError(_(
                    'Para remediação, adicione pelo menos uma linha com as novas dimensões.'
                ))

        # Quebra com sobras: obrigatório ter pelo menos 1 linha
        if self.scrap_type == 'break' and self.has_leftover:
            if not self.scrap_line_ids:
                raise UserError(_(
                    'Indicou que existem sobras. Adicione pelo menos uma linha ou desmarque a opção.'
                ))

        # Validar dimensões das linhas (se existirem)
        for line in self.scrap_line_ids:
            if not line.length or not line.width:
                raise UserError(_(
                    'Todas as linhas devem ter comprimento e largura preenchidos.'
                ))

        # Validar colisão de lot_name com base.lot.group existente
        self._check_lot_name_collision()

        # Validar que o total de área das sobras não ultrapassa o scrap_qty
        if self.scrap_line_ids:
            total_area = sum(line.area for line in self.scrap_line_ids)
            if total_area > self.scrap_qty:
                raise UserError(_(
                    'O total das sobras (%(total).4f) ultrapassa a quantidade original (%(qty).4f).',
                    total=total_area, qty=self.scrap_qty
                ))

        # Capturar grupos do lote original ANTES do super (referência para herança)
        orig_lot = self.lot_id
        orig_pg = orig_lot.price_group_id if orig_lot else False
        orig_bg = orig_pg.base_lot_group_id if orig_pg else False

        # Scrap standard (remove stock original)
        res = super().action_validate()

        # Se há linhas de saída, criar picking de entrada
        if self.scrap_line_ids:
            self._create_scrap_entry()
            self._inherit_groups_from_original(orig_pg, orig_bg)

        return res

    def _check_lot_name_collision(self):
        """Bloqueia validação se alguma scrap_line tiver lot_name que já existe
        como base.lot.group para o mesmo produto.

        Evita a sobrescrita de dados de pricing num grupo base existente quando
        o sistema reutiliza por nome+produto durante a criação dos novos lotes.
        """
        self.ensure_one()
        if not self.scrap_line_ids:
            return

        checked = set()
        for line in self.scrap_line_ids:
            key = (line.product_id.id, line.lot_name)
            if key in checked:
                continue
            checked.add(key)
            existing = self.env['base.lot.group'].sudo().search([
                ('product_id', '=', line.product_id.id),
                ('base_lot_name', '=', line.lot_name),
            ], limit=1)
            if existing:
                raise UserError(_(
                    "Já existe um Grupo Base de Lote '%(name)s' para o produto "
                    "'%(product)s'. Altere o nome do lote na linha de sobra para "
                    "evitar sobrescrita de dados existentes."
                ) % {
                    'name': line.lot_name,
                    'product': line.product_id.display_name,
                })

    def _inherit_groups_from_original(self, orig_pg, orig_bg):
        """Os base.lot.group e lot.price.group criados para os lotes novos
        (sobras de quebra ou remediação) herdam dos grupos do lote original
        os campos de pricing editáveis:

        - base.lot.group ← manual_sale_price, manual_pcmp, margin, list_price
        - lot.price.group ← use_base_pricing, margin, list_price

        Grupos colidentes com siblings do mesmo base_lot_name já partilham os
        mesmos valores via base_lot_group, por isso o write é idempotente.
        """
        self.ensure_one()
        if not self.entry_picking_id:
            return

        new_lots = self.entry_picking_id.move_line_ids.mapped('lot_id')
        if not new_lots:
            return

        new_pgs = new_lots.mapped('price_group_id')
        new_bgs = new_pgs.mapped('base_lot_group_id')

        if orig_bg and new_bgs:
            new_bgs.sudo().write({
                'manual_sale_price': orig_bg.manual_sale_price,
                'manual_pcmp': orig_bg.manual_pcmp,
                'margin': orig_bg.margin,
                'list_price': orig_bg.list_price,
            })

        if orig_pg and new_pgs:
            new_pgs.sudo().write({
                'use_base_pricing': orig_pg.use_base_pricing,
                'margin': orig_pg.margin,
                'list_price': orig_pg.list_price,
            })

    # ========================================
    # CRIAÇÃO DO PICKING DE ENTRADA
    # ========================================

    def _create_scrap_entry(self):
        """Criar picking de entrada com base nas scrap_line_ids"""
        self.ensure_one()

        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'incoming'),
            ('warehouse_id.company_id', '=', self.company_id.id),
        ], limit=1)

        if not picking_type:
            raise UserError(_('Tipo de operação de recepção não encontrado.'))

        source_location = self.scrap_location_id
        if not source_location:
            raise UserError(_('Localização de descarte não encontrada.'))

        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': source_location.id,
            'location_dest_id': self.location_id.id,
            'origin': _('Scrap %s (%s)') % (self.name, dict(self._fields['scrap_type'].selection).get(self.scrap_type)),
            'scrap_id': self.id,
        })

        for line in self.scrap_line_ids:
            product = line.product_id
            product_form = product.product_form if hasattr(product, 'product_form') else 'none'
            uom = product.uom_id

            self.env['stock.move'].create({
                'picking_id': picking.id,
                'product_id': product.id,
                'product_uom_qty': line.area,
                'product_uom': uom.id,
                'name': product.display_name,
                'location_id': source_location.id,
                'location_dest_id': self.location_id.id,
                'lot_name': line.lot_name or '',
                'length': line.length,
                'width': line.width,
                'thickness': line.thickness,
                'units_qty': line.units_qty or 1,
                'price_unit': line.price_unit,
                'scrap_transformation_line_id': line.id,
            })

        picking.action_confirm()

        for move in picking.move_ids:
            if not move.move_line_ids:
                self.env['stock.move.line'].create({
                    'move_id': move.id,
                    'picking_id': picking.id,
                    'product_id': move.product_id.id,
                    'product_uom_id': move.product_uom.id,
                    'location_id': move.location_id.id,
                    'location_dest_id': move.location_dest_id.id,
                    'length': move.length,
                    'width': move.width,
                    'thickness': move.thickness,
                    'units_qty': move.units_qty,
                })
            else:
                for ml in move.move_line_ids:
                    vals_update = {}
                    if not ml.length and move.length:
                        vals_update['length'] = move.length
                    if not ml.width and move.width:
                        vals_update['width'] = move.width
                    if not ml.thickness and move.thickness:
                        vals_update['thickness'] = move.thickness
                    if not ml.units_qty and move.units_qty:
                        vals_update['units_qty'] = move.units_qty
                    if vals_update:
                        ml.write(vals_update)

        picking.with_context(
            from_scrap=True,
            skip_backorder=True,
            picking_ids_not_to_backorder=picking.ids,
        ).button_validate()

        self.entry_picking_id = picking.id

        type_label = 'Quebra (sobras)' if self.scrap_type == 'break' else 'Remediação'
        _logger.info(
            "%s scrap %s: picking de entrada %s criado com %d linhas",
            type_label, self.name, picking.name, len(self.scrap_line_ids)
        )
