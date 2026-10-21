# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import float_compare
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    """
    Extensão do stock.picking para mh_purchase.

    NOTA: A lógica PCMP é controlada pelo mh_stock_valuation.
    Este módulo apenas bloqueia pickings de mercadoria que devem
    passar pelo Import Document.
    """
    _inherit = 'stock.picking'

    no_cost_validation = fields.Boolean(
        related='purchase_id.no_cost_validation',
        string='Sem Validação de Custos',
    )

    has_stone_products = fields.Boolean(
        string='Tem Produtos de Pedra',
        compute='_compute_has_stone_products',
        store=False,
        help='Indica se o picking tem produtos com product_form diferente de none'
    )

    @api.depends('move_ids', 'move_ids.product_id', 'move_ids.product_id.product_form')
    def _compute_has_stone_products(self):
        """Verifica se o picking tem produtos de pedra (product_form != 'none')"""
        for picking in self:
            picking.has_stone_products = any(
                move.product_id and
                hasattr(move.product_id, 'product_form') and
                move.product_id.product_form != 'none'
                for move in picking.move_ids
            )

    def action_print_stickers(self):
        """Abrir wizard para escolher tipo de impressão de stickers (PDF/ZPL)"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Imprimir Stickers',
            'res_model': 'sticker.print.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_picking_id': self.id,
            },
        }

    def action_print_guia_recepcao(self):
        """Imprimir Listagem de Pedras"""
        self.ensure_one()

        if self.state != 'done':
            raise UserError("Este relatório só está disponível para pickings validados.")

        if not self.purchase_id:
            raise UserError("Este relatório só está disponível para pickings que provêm de uma Ordem de Compra.")

        # Retornar a ação do relatório
        return self.env.ref('mh_stone_reports.action_report_stone_picking').report_action(self)

    def _check_move_price_matches_po(self):
        """Bloqueia a validação se o custo de uma linha (move.price_unit)
        diferir do preço da linha de compra (purchase.order.line),
        convertido para a moeda da empresa quando necessário.

        Aplica-se a recibos de compra (incoming) com linha de PO.
        """
        precision = self.env['decimal.precision'].precision_get('Product Price')
        for picking in self:
            if picking.picking_type_code != 'incoming':
                continue
            mismatches = []
            for move in picking.move_ids:
                pol = move.purchase_line_id
                if not pol:
                    continue
                company = move.company_id or picking.company_id
                # Só validamos quando a PO está na MESMA moeda da empresa.
                # Em moeda estrangeira a conversão introduz diferenças de taxa
                # que dariam falsos positivos, por isso ignoramos.
                if pol.currency_id and pol.currency_id != company.currency_id:
                    continue
                if float_compare(move.price_unit, pol.price_unit, precision_digits=precision) != 0:
                    lots = move.move_line_ids.lot_id.mapped('name')
                    if not lots:
                        lots = [l for l in move.move_line_ids.mapped('lot_name') if l]
                    label = move.product_id.display_name
                    if lots:
                        label += " [%s]" % ", ".join(lots)
                    mismatches.append((label, move.price_unit, pol.price_unit))
            if mismatches:
                detalhe = "\n".join(
                    "  • %s: custo de recepção %.2f  ≠  preço da PO %.2f" % m
                    for m in mismatches)
                raise UserError(
                    "Não é possível validar o picking %s.\n\n"
                    "As seguintes linhas têm o custo de recepção diferente do "
                    "preço da Ordem de Compra:\n\n%s\n\n"
                    "Acerte o custo destas linhas para coincidir com a PO antes "
                    "de validar."
                    % (picking.name, detalhe))

    def button_validate(self):
        """Valida receções pelo fluxo standard, mantendo controlos de origem e preço."""
        # Bloqueador: custo de recepção tem de coincidir com o preço da PO
        self._check_move_price_matches_po()

        for picking in self:
            # Bloquear entradas manuais (sem purchase_id, scrap_id nem return_id).
            # Excepção: Stock Inicial (is_initial_stock) é uma origem legítima.
            # Bypass: contexto 'bypass_manual_picking_check' para correcções
            # pontuais (ex: adicionar placas esquecidas a IMP já fechado).
            if (picking.picking_type_code == 'incoming' and
                    not picking.purchase_id and
                    not picking.scrap_id and
                    not picking.return_id and
                    not picking.is_initial_stock and
                    not getattr(picking, 'transformation_id', False) and
                    not self.env.context.get('bypass_manual_picking_check')):
                raise UserError(
                    "Este picking de entrada não pode ser validado manualmente!\n\n"
                    f"Picking: {picking.name}\n\n"
                    "Pickings de entrada só podem ser validados quando associados a:\n"
                    "  - Um Pedido de Compra\n"
                    "  - Um Pedido de Compra (via Import Document)\n"
                    "  - Um Descarte (Quebra/Remediação com sobras)\n"
                    "  - Uma Devolução de Cliente\n"
                    "  - Um Documento de Transformação\n"
                    "  - Stock Inicial\n\n"
                    "Não é permitido criar e validar entradas de stock sem origem."
                )

        return super().button_validate()
