# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class MaterialConsumption(models.Model):
    _name = 'material.consumption'
    _description = 'Consumo de Material'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Referência',
        required=True,
        copy=False,
        readonly=True,
        default='Novo',
    )
    date = fields.Datetime(
        string='Data',
        required=True,
        default=fields.Datetime.now,
        tracking=True,
    )
    user_id = fields.Many2one(
        'res.users',
        string='Solicitado por',
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    department = fields.Char(
        string='Departamento',
    )
    notes = fields.Text(
        string='Observações',
    )
    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('confirmed', 'Confirmado'),
        ('done', 'Concluído'),
        ('cancelled', 'Cancelado'),
    ], string='Estado', default='draft', required=True, tracking=True)

    line_ids = fields.One2many(
        'material.consumption.line',
        'consumption_id',
        string='Linhas de Consumo',
    )
    picking_ids = fields.One2many(
        'stock.picking',
        'material_consumption_id',
        string='Movimentos de Stock',
        readonly=True,
        copy=False,
    )
    picking_count = fields.Integer(
        string='Nº Pickings',
        compute='_compute_picking_count',
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Armazém',
        required=True,
        default=lambda self: self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.company.id)], limit=1
        ),
        tracking=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        required=True,
        default=lambda self: self.env.company,
    )
    consumption_location_id = fields.Many2one(
        'stock.location',
        string='Localização de Consumo',
        compute='_compute_consumption_location_id',
    )
    line_count = fields.Integer(
        string='Nº Linhas',
        compute='_compute_line_count',
    )

    @api.depends('warehouse_id')
    def _compute_consumption_location_id(self):
        for rec in self:
            rec.consumption_location_id = rec.warehouse_id.lot_stock_id

    @api.depends('line_ids')
    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)

    @api.depends('picking_ids')
    def _compute_picking_count(self):
        for rec in self:
            rec.picking_count = len(rec.picking_ids)

    def unlink(self):
        raise UserError(_('Não é permitido eliminar registos de consumo de material.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Novo') == 'Novo':
                vals['name'] = self.env['ir.sequence'].next_by_code('material.consumption') or 'Novo'
        return super().create(vals_list)

    def _get_active_picking(self):
        """Retorna o picking activo (não cancelado) mais recente."""
        self.ensure_one()
        return self.picking_ids.filtered(lambda p: p.state != 'cancel').sorted('id', reverse=True)[:1]

    # ──────────────────────────────────────────────
    # Verificação de stock
    # ──────────────────────────────────────────────

    def _get_source_location(self):
        """Retorna a localização de stock principal do armazém (lot_stock_id)."""
        self.ensure_one()
        location = self.warehouse_id.lot_stock_id
        if not location:
            raise UserError(_(
                'Não foi encontrada a localização de stock principal do armazém "%s".'
            ) % self.warehouse_id.name)
        return location

    def _get_dest_location(self):
        """Retorna a localização destino (customer) para saída de stock."""
        self.ensure_one()
        dest_location = self.env.ref(
            'mh_internal_consumption.stock_location_consumption', raise_if_not_found=False
        )
        if not dest_location:
            raise UserError(_(
                'Não foi encontrada a localização destino de consumo interno.\n'
                'Verifique se o módulo foi instalado correctamente.'
            ))
        return dest_location

    def _check_stock_availability(self):
        """Verifica se há stock livre suficiente para todas as linhas.
        Usa free_qty (em mão - reservada) para não contar stock já reservado.
        Valida stock na localização principal do armazém (lot_stock_id).
        """
        self.ensure_one()
        source_location = self._get_source_location()
        errors = []
        for line in self.line_ids:
            if line.product_id.type != 'consu':
                errors.append(_(
                    '• %s: Produto do tipo "%s" não tem controle de stock. '
                    'Altere para tipo "Armazenável" para controlar stock.'
                ) % (line.product_id.display_name, line.product_id.type))
                continue

            product_ctx = line.product_id.with_context(location=source_location.id)
            free_qty = product_ctx.free_qty

            if free_qty < line.quantity:
                errors.append(_(
                    '• %s: Disponível %.2f %s (livre) na localização "%s", solicitado %.2f %s.'
                ) % (
                    line.product_id.display_name,
                    free_qty,
                    line.uom_id.name,
                    source_location.display_name,
                    line.quantity,
                    line.uom_id.name,
                ))

        if errors:
            raise UserError(_(
                'Não é possível confirmar o consumo de material:\n\n%s'
            ) % '\n'.join(errors))

    # ──────────────────────────────────────────────
    # Acções de workflow
    # ──────────────────────────────────────────────

    def action_confirm(self):
        """Rascunho → Confirmado.
        1. Valida que existem linhas
        2. Verifica stock disponível no armazém principal
        3. Cria picking (confirmado, mas NÃO validado)
        """
        for rec in self:
            if not rec.line_ids:
                raise UserError(_('Não pode confirmar sem linhas de consumo.'))

            rec._check_stock_availability()

            picking = rec._create_stock_picking()

            rec.state = 'confirmed'
            _logger.info(
                "Consumo de material %s confirmado. Picking %s criado (aguarda validação).",
                rec.name, picking.name,
            )

    def action_done(self):
        """Confirmado → Concluído.
        Valida o picking (efectiva a transferência de stock para localização de consumo).
        """
        for rec in self:
            active_picking = rec._get_active_picking()
            if not active_picking:
                raise UserError(_('Não existe movimento de stock para validar.'))

            rec._validate_picking(active_picking)

            rec.state = 'done'
            _logger.info(
                "Consumo de material %s concluído. Picking %s validado.",
                rec.name, active_picking.name,
            )

    def action_cancel(self):
        """Draft/Confirmed → Cancelado.
        - Não pode cancelar se estado = done
        - Se tiver picking não done, cancela o picking
        """
        for rec in self:
            if rec.state == 'done':
                raise UserError(_(
                    'Não pode cancelar o consumo %s!\n'
                    'O consumo já foi concluído e o stock já foi movimentado.'
                ) % rec.name)

            for picking in rec.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel')):
                picking.action_cancel()

            rec.state = 'cancelled'

    def action_draft(self):
        """Cancelado → Rascunho. Mantém referências de pickings como histórico."""
        for rec in self:
            rec.state = 'draft'

    # ──────────────────────────────────────────────
    # Smart buttons
    # ──────────────────────────────────────────────

    def action_view_pickings(self):
        """Abre os movimentos de stock associados."""
        self.ensure_one()
        if len(self.picking_ids) == 1:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'view_mode': 'form',
                'res_id': self.picking_ids.id,
                'target': 'current',
            }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.picking_ids.ids)],
            'target': 'current',
            'name': _('Movimentos de Stock'),
        }

    # ──────────────────────────────────────────────
    # Métodos auxiliares de stock
    # ──────────────────────────────────────────────

    def _get_picking_type(self):
        """Retorna o tipo de operação para transferência interna."""
        self.ensure_one()
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('company_id', '=', self.company_id.id),
        ], limit=1)

        if not picking_type:
            raise UserError(_('Não foi encontrado um tipo de operação de transferência interna.'))

        return picking_type

    def _create_stock_picking(self):
        """Cria stock.picking e confirma (sem validar).
        Origem: localização principal do armazém (lot_stock_id).
        Destino: localização interna de consumo.
        """
        self.ensure_one()

        picking_type = self._get_picking_type()
        source_location = self._get_source_location()
        dest_location = self._get_dest_location()

        move_lines = []
        for line in self.line_ids:
            move_lines.append((0, 0, {
                'name': f"{self.name}: {line.product_id.display_name}",
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'product_uom': line.uom_id.id,
                'location_id': source_location.id,
                'location_dest_id': dest_location.id,
            }))

        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': source_location.id,
            'location_dest_id': dest_location.id,
            'origin': self.name,
            'material_consumption_id': self.id,
            'scheduled_date': self.date,
            'move_ids': move_lines,
        })

        picking.action_confirm()
        picking.action_assign()

        return picking

    def _validate_picking(self, picking):
        """Valida o picking existente (efectiva a transferência de stock)."""
        self.ensure_one()

        if picking.state == 'done':
            return

        if picking.state == 'cancel':
            raise UserError(_(
                'O movimento de stock %s foi cancelado. Não pode concluir.'
            ) % picking.name)

        for move in picking.move_ids:
            move.quantity = move.product_uom_qty

        picking.button_validate()


class MaterialConsumptionLine(models.Model):
    _name = 'material.consumption.line'
    _description = 'Linha de Consumo de Material'

    consumption_id = fields.Many2one(
        'material.consumption',
        string='Consumo',
        required=True,
        ondelete='cascade',
    )
    product_id = fields.Many2one(
        'product.product',
        string='Produto',
        required=True,
    )
    quantity = fields.Float(
        string='Quantidade',
        required=True,
        default=1.0,
        digits='Product Unit of Measure',
    )
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unidade',
        required=True,
    )
    location_id = fields.Many2one(
        'stock.location',
        string='Localização Origem',
    )
    free_qty = fields.Float(
        string='Disponível',
        compute='_compute_free_qty',
        digits='Product Unit of Measure',
    )
    notes = fields.Char(
        string='Notas',
    )

    @api.depends('product_id', 'consumption_id.warehouse_id')
    def _compute_free_qty(self):
        for line in self:
            if line.product_id and line.product_id.type == 'consu' and line.consumption_id.warehouse_id:
                source_loc = line.consumption_id.warehouse_id.lot_stock_id
                if source_loc:
                    line.free_qty = line.product_id.with_context(location=source_loc.id).free_qty
                else:
                    line.free_qty = 0.0
            else:
                line.free_qty = 0.0

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.uom_id = self.product_id.uom_id
