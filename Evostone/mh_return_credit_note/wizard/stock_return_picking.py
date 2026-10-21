# Copyright 2025 MH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class StockReturnPickingLine(models.TransientModel):
    _inherit = 'stock.return.picking.line'

    product_form = fields.Selection(
        related='product_id.product_tmpl_id.product_form',
        string='Forma do Produto',
        readonly=True,
    )

    lot_id = fields.Many2one(
        'stock.lot',
        string='SN',
        compute='_compute_lot_id',
        store=False,
        help='Lote associado ao movimento original (para vendas)'
    )

    lot_name = fields.Char(
        string='Lote',
        compute='_compute_lot_name',
        store=False,
        help='Nome do lote associado ao movimento original (para compras)'
    )

    # Campos de dimensão (para filtro em compras)
    units_qty = fields.Integer(
        string='Quantidade',
        compute='_compute_dimensions',
        store=False,
        help='Quantidade de unidades do movimento original'
    )

    length = fields.Float(
        string='Comprimento',
        compute='_compute_dimensions',
        store=False,
        digits='Dimensions',
        help='Comprimento do movimento original'
    )

    width = fields.Float(
        string='Largura',
        compute='_compute_dimensions',
        store=False,
        digits='Dimensions',
        help='Largura do movimento original'
    )

    thickness = fields.Float(
        string='Espessura',
        compute='_compute_dimensions',
        store=False,
        digits='Dimensions',
        help='Espessura do movimento original'
    )

    @api.depends('move_id', 'move_id.units_qty', 'move_id.length', 'move_id.width', 'move_id.thickness')
    def _compute_dimensions(self):
        """Obter dimensões do stock.move original"""
        for line in self:
            if line.move_id:
                line.units_qty = line.move_id.units_qty or 0
                line.length = line.move_id.length or 0.0
                line.width = line.move_id.width or 0.0
                line.thickness = line.move_id.thickness or 0.0
            else:
                line.units_qty = 0
                line.length = 0.0
                line.width = 0.0
                line.thickness = 0.0

    @api.depends('move_id', 'move_id.move_line_ids', 'move_id.move_line_ids.lot_id')
    def _compute_lot_id(self):
        """Obter lot_id do stock.move original (para vendas)"""
        for line in self:
            if line.move_id and line.move_id.move_line_ids:
                # Pegar o primeiro lote das move_lines
                lot = line.move_id.move_line_ids.mapped('lot_id')[:1]
                line.lot_id = lot.id if lot else False
            else:
                line.lot_id = False

    @api.depends('move_id', 'move_id.lot_name')
    def _compute_lot_name(self):
        """Obter lot_name do stock.move original (para compras)"""
        for line in self:
            if line.move_id:
                line.lot_name = line.move_id.lot_name or False
            else:
                line.lot_name = False


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    # ===== CAMPOS EXISTENTES =====
    create_credit_note = fields.Boolean(
        string='Criar Nota de Crédito',
        default=False,
        help='Se marcado, cria automaticamente uma nota de crédito com as quantidades devolvidas'
    )

    credit_note_reason = fields.Char(
        string='Motivo',
        default='Devolução de mercadoria',
        help='Motivo a incluir na nota de crédito'
    )

    credit_note_date = fields.Date(
        string='Data da Nota de Crédito',
        default=fields.Date.today,
        help='Data da nota de crédito (padrão: hoje)'
    )

    credit_note_journal_id = fields.Many2one(
        'account.journal',
        string='Diário',
        domain="[('type', 'in', ['sale', 'purchase']), ('company_id', '=', company_id)]",
        help='Diário para a nota de crédito'
    )

    company_id = fields.Many2one(
        'res.company',
        related='picking_id.company_id',
        readonly=True
    )

    is_purchase_picking = fields.Boolean(
        string='É Devolução de Compra',
        compute='_compute_is_purchase_picking',
        store=False,
        help='Indica se é uma devolução de compra (incoming) ou venda (outgoing)'
    )

    @api.depends('picking_id', 'picking_id.picking_type_code')
    def _compute_is_purchase_picking(self):
        """Determina se o picking é de compra (incoming) ou venda (outgoing)"""
        for wizard in self:
            if wizard.picking_id:
                wizard.is_purchase_picking = wizard.picking_id.picking_type_code == 'incoming'
            else:
                wizard.is_purchase_picking = False

    can_create_credit_note = fields.Boolean(
        string='Pode Criar Nota de Crédito',
        compute='_compute_can_create_credit_note',
        help='Indica se é possível criar nota de crédito para este picking'
    )

    # ===== NOVOS CAMPOS PARA SUPORTE A COMPRAS =====
    credit_note_type = fields.Selection(
        selection=[
            ('sale', 'Cliente (Venda)'),
            ('purchase', 'Fornecedor (Compra)'),
        ],
        string='Tipo de Nota de Crédito',
        compute='_compute_credit_note_type',
        store=False,
        help='Tipo de nota de crédito baseado no picking original'
    )

    can_create_sale_credit_note = fields.Boolean(
        string='Pode Criar NC Venda',
        compute='_compute_can_create_credit_note',
        help='Indica se é possível criar nota de crédito de venda'
    )

    can_create_purchase_credit_note = fields.Boolean(
        string='Pode Criar NC Compra',
        compute='_compute_can_create_credit_note',
        help='Indica se é possível criar nota de crédito de compra'
    )

    # ===== MÉTODOS COMPUTADOS =====
    @api.depends('picking_id')
    def _compute_credit_note_type(self):
        """Determina automaticamente o tipo baseado no picking"""
        for wizard in self:
            picking = wizard.picking_id
            if picking.picking_type_code == 'outgoing' and picking.sale_id:
                wizard.credit_note_type = 'sale'
            elif picking.picking_type_code == 'incoming' and picking.purchase_id:
                wizard.credit_note_type = 'purchase'
            else:
                wizard.credit_note_type = False

    @api.depends('picking_id')
    def _compute_can_create_credit_note(self):
        """Verificar se o picking tem fatura associada para criar nota de crédito"""
        for wizard in self:
            can_sale = False
            can_purchase = False

            if wizard.picking_id:
                picking = wizard.picking_id

                # VENDAS: outgoing + sale_id + faturas postadas
                if picking.picking_type_code == 'outgoing' and picking.sale_id:
                    invoices = picking.sale_id.invoice_ids.filtered(
                        lambda i: i.move_type == 'out_invoice' and i.state == 'posted'
                    )
                    can_sale = bool(invoices)

                # COMPRAS: incoming + purchase_id + faturas postadas
                elif picking.picking_type_code == 'incoming' and picking.purchase_id:
                    invoices = picking.purchase_id.invoice_ids.filtered(
                        lambda i: i.move_type == 'in_invoice' and i.state == 'posted'
                    )
                    can_purchase = bool(invoices)

            wizard.can_create_sale_credit_note = can_sale
            wizard.can_create_purchase_credit_note = can_purchase
            wizard.can_create_credit_note = can_sale or can_purchase

    @api.onchange('create_credit_note', 'credit_note_type')
    def _onchange_create_credit_note(self):
        """Definir diário padrão baseado no tipo de nota"""
        if self.create_credit_note and not self.credit_note_journal_id:
            if self.credit_note_type == 'sale':
                journal_type = 'sale'
            elif self.credit_note_type == 'purchase':
                journal_type = 'purchase'
            else:
                journal_type = None

            if journal_type:
                journal = self.env['account.journal'].search([
                    ('type', '=', journal_type),
                    ('company_id', '=', self.company_id.id)
                ], limit=1)

                if journal:
                    self.credit_note_journal_id = journal

    # ===== AUTO-PREENCHER QUANTIDADE PARA PRODUTOS COM DIMENSÕES =====
    def _prepare_stock_return_picking_line_vals_from_move(self, stock_move):
        """Override para auto-preencher quantidade quando product_form != 'none'

        Produtos com dimensões (blocos, placas, bandas, tiles) devem ter
        a quantidade preenchida automaticamente com o total devolvível,
        pois são rastreados por lote e não faz sentido devolver parcialmente.
        """
        vals = super()._prepare_stock_return_picking_line_vals_from_move(stock_move)

        # Verificar product_form do produto
        product_form = stock_move.product_id.product_tmpl_id.product_form
        if product_form and product_form != 'none':
            # Calcular quantidade já devolvida
            quantity_returned = sum(
                m.quantity for m in stock_move.move_dest_ids
                if m.origin_returned_move_id == stock_move
                and m.state in ('partially_available', 'assigned', 'done')
            )
            # Quantidade devolvível = entregue - já devolvida
            returnable_qty = stock_move.quantity - quantity_returned
            vals['quantity'] = max(0, returnable_qty)

        return vals

    # ===== REFORÇO: GUARD COMUM =====
    def _check_return_allowed(self):
        """Defesa em profundidade: bloqueia devoluções indevidas em TODOS os
        pontos de entrada do wizard (action_create_returns,
        action_create_returns_all, action_create_exchanges), mesmo que a acção
        seja disparada por outra via que não o botão da vista."""
        picking = self.picking_id
        if not picking:
            return
        # Não devolver uma saída já totalmente devolvida (evita duplicar
        # devolução + nota de crédito).
        if picking.picking_type_code == 'outgoing' and picking.fully_returned:
            raise UserError(_(
                'A saída "%s" já está totalmente devolvida — não é '
                'possível criar outra devolução.'
            ) % (picking.name or ''))
        # Não devolver uma devolução de venda.
        if picking.is_sale_return:
            raise UserError(_(
                'O documento "%s" é uma devolução de venda — não se '
                'devolve uma devolução de venda.'
            ) % (picking.name or ''))
        # Não gerar NC pela devolução se a factura de origem JÁ está
        # totalmente creditada (evita NC duplicada quando a 1ª NC foi feita
        # directamente na factura). A devolução física pode ser feita à parte
        # desmarcando "Criar Nota de Crédito".
        if self.create_credit_note:
            source = self._get_return_source_invoice()
            if source and source.is_fully_credited:
                ncs = source.reversal_move_ids.filtered(lambda m: m.state != 'cancel')
                raise UserError(_(
                    'A factura "%(inv)s" já está totalmente creditada pela(s) '
                    'nota(s) de crédito: %(ncs)s.\n\nDesmarque "Criar Nota de '
                    'Crédito" para fazer apenas a devolução física, ou cancele '
                    'a nota de crédito existente.'
                ) % {
                    'inv': source.name or '',
                    'ncs': ', '.join(ncs.mapped('name')) or _('(rascunho)'),
                })

    def _get_return_source_invoice(self):
        """Factura de origem que a NC da devolução reverteria (a mais recente
        postada da venda/compra do picking). Espelha a lógica usada em
        _create_sale_credit_note / _create_purchase_credit_note."""
        picking = self.picking_id
        if not picking:
            return self.env['account.move']
        if picking.picking_type_code == 'outgoing' and picking.sale_id:
            invoices = picking.sale_id.invoice_ids.filtered(
                lambda i: i.move_type == 'out_invoice' and i.state == 'posted')
        elif picking.picking_type_code == 'incoming' and picking.purchase_id:
            invoices = picking.purchase_id.invoice_ids.filtered(
                lambda i: i.move_type == 'in_invoice' and i.state == 'posted')
        else:
            return self.env['account.move']
        if not invoices:
            return self.env['account.move']
        return invoices.sorted(
            key=lambda i: i.invoice_date or i.create_date, reverse=True)[0]

    # ===== MÉTODO PRINCIPAL (OVERRIDE) =====
    def action_create_returns(self):
        """Override para criar nota de crédito após devolução."""
        self._check_return_allowed()

        # Chamar método original para criar o picking de devolução
        result = super().action_create_returns()

        # Se marcou criar nota de crédito, criar após o return picking
        if self.create_credit_note:
            self._create_credit_note_from_return(result)

        return result

    def action_create_returns_all(self):
        """Reforço: bloquear 'Devolver tudo' indevido antes de criar."""
        self._check_return_allowed()
        return super().action_create_returns_all()

    def action_create_exchanges(self):
        """Reforço: bloquear 'Troca' (exchange) indevida antes de criar."""
        self._check_return_allowed()
        return super().action_create_exchanges()

    # ===== ROUTER: DIRECIONA PARA O MÉTODO CORRETO =====
    def _create_credit_note_from_return(self, return_result):
        """
        Router: Direciona para o método correto baseado no tipo.
        Segue o princípio de Single Responsibility.
        """
        if self.credit_note_type == 'sale':
            return self._create_sale_credit_note(return_result)
        elif self.credit_note_type == 'purchase':
            return self._create_purchase_credit_note(return_result)
        else:
            _logger.warning("Tipo de nota de crédito não identificado")
            return

    # ===== MÉTODO PARA VENDAS (out_refund) =====
    def _create_sale_credit_note(self, return_result):
        """Criar nota de crédito de VENDA usando wizard nativo de reversão"""
        return_picking = self._get_return_picking(return_result)
        if not return_picking:
            return

        origin_picking = self.picking_id
        sale_order = origin_picking.sale_id

        if not sale_order:
            raise UserError(_("Não é possível criar nota de crédito: picking sem venda associada."))

        # Obter fatura postada mais recente
        invoices = sale_order.invoice_ids.filtered(
            lambda i: i.move_type == 'out_invoice' and i.state == 'posted'
        )
        if not invoices:
            raise UserError(_("Não é possível criar nota de crédito: venda sem faturas postadas."))

        source_invoice = invoices.sorted(key=lambda i: i.invoice_date or i.create_date, reverse=True)[0]

        # Usar método híbrido: reversão nativa + quantidades parciais
        credit_note = self._create_credit_note_via_reversal(source_invoice, return_picking, origin_picking)
        return self._finalize_credit_note(credit_note, return_picking)

    # ===== MÉTODO PARA COMPRAS (in_refund) =====
    def _create_purchase_credit_note(self, return_result):
        """Criar nota de crédito de COMPRA usando wizard nativo de reversão"""
        return_picking = self._get_return_picking(return_result)
        if not return_picking:
            return

        origin_picking = self.picking_id
        purchase_order = origin_picking.purchase_id

        if not purchase_order:
            raise UserError(_("Não é possível criar nota de crédito: picking sem compra associada."))

        # Obter fatura postada mais recente
        invoices = purchase_order.invoice_ids.filtered(
            lambda i: i.move_type == 'in_invoice' and i.state == 'posted'
        )
        if not invoices:
            raise UserError(_("Não é possível criar nota de crédito: compra sem faturas postadas."))

        source_invoice = invoices.sorted(key=lambda i: i.invoice_date or i.create_date, reverse=True)[0]

        # Usar método híbrido: reversão nativa + quantidades parciais
        credit_note = self._create_credit_note_via_reversal(source_invoice, return_picking, origin_picking)
        return self._finalize_credit_note(credit_note, return_picking)

    # ===== MÉTODOS AUXILIARES =====
    def _get_return_picking(self, return_result):
        """Extrair picking de devolução do resultado"""
        if isinstance(return_result, dict) and return_result.get('res_id'):
            return self.env['stock.picking'].browse(return_result['res_id'])
        _logger.warning("Não foi possível obter o picking de devolução")
        return False

    def _create_credit_note_via_reversal(self, source_invoice, return_picking, origin_picking):
        """
        Criar NC usando o wizard nativo de reversão do Odoo.
        Garante que todos os campos são copiados correctamente da fatura original.
        """
        # 1. Criar wizard de reversão nativo
        reversal_wizard = self.env['account.move.reversal'].create({
            'move_ids': [(6, 0, [source_invoice.id])],
            'date': self.credit_note_date,
            'reason': self.credit_note_reason or f'Devolução {return_picking.name}',
            'journal_id': self.credit_note_journal_id.id if self.credit_note_journal_id else source_invoice.journal_id.id,
            'company_id': source_invoice.company_id.id,
        })

        # 2. Executar reversão (cria NC em draft)
        action = reversal_wizard.refund_moves()

        # 3. Obter a NC criada
        new_move_ids = action.get('res_id') or action.get('res_ids', [])
        if isinstance(new_move_ids, int):
            new_move_ids = [new_move_ids]

        if not new_move_ids:
            raise UserError(_("Erro ao criar nota de crédito via reversão."))

        credit_note = self.env['account.move'].browse(new_move_ids[0])

        # 4. Ajustar quantidades baseado na devolução
        self._adjust_credit_note_quantities(credit_note)

        # 5. Adicionar links ao picking e informação adicional
        credit_note.write({
            'return_picking_id': return_picking.id,
            'origin_picking_id': origin_picking.id,
            'narration': (
                f"Nota de crédito gerada automaticamente via devolução.\n"
                f"Picking original: {origin_picking.name}\n"
                f"Picking devolução: {return_picking.name}\n"
                f"Fatura original: {source_invoice.name}"
            ),
        })

        return credit_note

    def _adjust_credit_note_quantities(self, credit_note):
        """
        Ajustar quantidades da NC baseado nos produtos devolvidos.
        Remove linhas de produtos não devolvidos.

        Para VENDAS: Filtra por product_id E lot_id
        Para COMPRAS: Filtra por product_id, lot_name, units_qty, length, width, thickness
        """
        # Determinar se é venda ou compra
        is_purchase = credit_note.move_type == 'in_refund'

        # Mapear produtos devolvidos e suas quantidades
        returned_products = {}
        for line in self.product_return_moves:
            if line.quantity > 0:
                if is_purchase:
                    # COMPRAS: usar lot_name + dimensões
                    key = (
                        line.product_id.id,
                        line.lot_name or False,
                        line.units_qty or 0,
                        line.length or 0.0,
                        line.width or 0.0,
                        line.thickness or 0.0,
                    )
                else:
                    # VENDAS: usar lot_id
                    key = (line.product_id.id, line.lot_id.id if line.lot_id else False)
                returned_products[key] = line.quantity

        key_type = 'lot_name + dimensões' if is_purchase else 'lot_id'
        _logger.info(f"Produtos devolvidos (product_id, {key_type}): {returned_products}")

        # CRÍTICO: Invalidar cache para garantir que linhas estão disponíveis
        credit_note.invalidate_recordset(['invoice_line_ids', 'line_ids'])

        # Debug: verificar estado da NC
        _logger.info(f"NC ID: {credit_note.id}, State: {credit_note.state}")
        _logger.info(f"Total line_ids: {len(credit_note.line_ids)}")
        _logger.info(f"Total invoice_line_ids: {len(credit_note.invoice_line_ids)}")

        # Usar invoice_line_ids filtrado por produto (ignora seções e notas)
        product_lines = credit_note.invoice_line_ids.filtered(
            lambda l: l.product_id
        )

        _logger.info(f"Product lines encontradas: {len(product_lines)}")

        lines_to_remove = []
        lines_to_update = []

        for line in product_lines:
            product_id = line.product_id.id

            if is_purchase:
                # COMPRAS: usar lot_name + dimensões
                key = (
                    product_id,
                    line.lot_name or False,
                    line.units_qty or 0,
                    line.length or 0.0,
                    line.width or 0.0,
                    line.thickness or 0.0,
                )
                _logger.info(f"Linha: {line.name}, Key: {key}")
            else:
                # VENDAS: usar lot_id
                lot_key = line.lot_id.id if line.lot_id else False
                key = (product_id, lot_key)
                _logger.info(f"Linha: {line.name}, Produto ID: {product_id}, Lote (id): {lot_key}")

            if key in returned_products:
                # Manter linha mas ajustar quantidade
                lines_to_update.append((line, returned_products[key]))
                _logger.info(f"  -> Ajustar qty para {returned_products[key]}")
            else:
                # Tentar match apenas por product_id (para linhas sem lote/dimensões)
                if is_purchase:
                    key_fallback = (product_id, False, 0, 0.0, 0.0, 0.0)
                else:
                    key_fallback = (product_id, False)

                if key_fallback in returned_products:
                    lines_to_update.append((line, returned_products[key_fallback]))
                    _logger.info(f"  -> Ajustar qty para {returned_products[key_fallback]} (match por produto)")
                else:
                    # Remover linha (produto não devolvido)
                    lines_to_remove.append(line)
                    _logger.info(f"  -> Remover linha")

        # Aplicar actualizações de quantidade
        for line, qty in lines_to_update:
            line.with_context(check_move_validity=False).write({'quantity': qty})

        # Remover linhas não devolvidas
        if lines_to_remove:
            for line in lines_to_remove:
                line.with_context(check_move_validity=False).unlink()

        # Recomputar totais
        credit_note._compute_amount()

    def _finalize_credit_note(self, credit_note, return_picking):
        """Finalizar e vincular NC ao picking"""
        return_picking.credit_note_id = credit_note.id

        move_type_label = 'cliente' if credit_note.move_type == 'out_refund' else 'fornecedor'
        _logger.info(
            f"Nota de crédito ({move_type_label}) {credit_note.name} criada para devolução {return_picking.name}"
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Nota de Crédito Criada'),
                'message': _('Nota de crédito %s (%s) criada com sucesso.') % (credit_note.name, move_type_label),
                'type': 'success',
                'sticky': False,
            }
        }
