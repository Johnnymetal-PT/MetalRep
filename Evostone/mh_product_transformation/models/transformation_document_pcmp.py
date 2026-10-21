# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class TransformationDocumentPCMP(models.AbstractModel):
    """Mixin: Criação de Landed Cost para Transformações

    Responsável por:
    - Criação de stock.landed.cost seguindo padrão Odoo 18
    - Distribuição de custos via landed cost (não manual)

    NOTA: O cálculo real de PCMP é feito pelo mh_stock_valuation
    via stock.landed.cost.button_validate() -> _update_pcmp()
    """
    _name = 'transformation.document.pcmp'
    _description = 'Transformation Document Landed Costs Mixin'

    landed_cost_id = fields.Many2one(
        'stock.landed.cost',
        string='Landed Cost',
        readonly=True,
        copy=False,
        help='Landed cost criado para distribuir custos adicionais'
    )

    def _create_transformation_landed_cost(self):
        """
        Cria stock.landed.cost para transformação.
        Similar a import.document._create_landed_cost()

        Pré-condição: Picking IN deve estar validado (state='done')

        Returns:
            stock.landed.cost: Landed cost criado ou False se não há custos
        """
        self.ensure_one()

        # 1. Buscar picking IN validado
        picking_in = self.picking_ids.filtered(
            lambda p: p.location_id == self.location_production_id and
                     p.location_dest_id == self.location_dest_id and
                     p.state == 'done'
        )

        if not picking_in:
            raise UserError(_("Nenhum picking de entrada validado encontrado!"))

        # Verificar se há POs de serviço
        if not self.service_purchase_order_ids:
            _logger.info(f"Transformação {self.name}: Sem POs de serviço para criar landed cost")
            return False

        # 2. Criar linhas de custo das POs de serviço
        cost_lines = []

        for po in self.service_purchase_order_ids:
            for line in po.order_line:
                if not line.product_id or line.price_subtotal <= 0:
                    continue

                # Converter para moeda da empresa se necessário
                if po.currency_id != self.currency_id:
                    price = po.currency_id._convert(
                        line.price_subtotal,
                        self.currency_id,
                        self.company_id,
                        self.date_document or fields.Date.today()
                    )
                else:
                    price = line.price_subtotal

                # Obter conta contabilística
                account = (
                    line.product_id.property_account_expense_id or
                    line.product_id.categ_id.property_account_expense_categ_id or
                    self.company_id.property_stock_account_input_categ_id
                )

                # Obter método de split
                split_method = getattr(
                    line.product_id,
                    'split_method_landed_cost',
                    False
                ) or 'by_current_cost_price'

                cost_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': f"{po.name}: {line.name}",
                    'price_unit': price,
                    'split_method': split_method,
                    'account_id': account.id if account else False,
                }))

        if not cost_lines:
            _logger.info(f"Transformação {self.name}: Sem custos adicionais para distribuir")
            return False

        # 3. Criar landed cost
        landed_cost = self.env['stock.landed.cost'].create({
            'date': self.date_document or fields.Date.today(),
            'picking_ids': [(6, 0, picking_in.ids)],
            'cost_lines': cost_lines,
        })

        self.landed_cost_id = landed_cost.id
        _logger.info(
            f"Landed Cost {landed_cost.name} criado para transformação {self.name} "
            f"com {len(cost_lines)} linha(s) de custo"
        )

        return landed_cost

    def _update_output_lines_pcmp(self):
        """
        Actualiza pcmp_calculated nas output lines após validação do landed cost.

        Isto é para fins de auditoria/relatórios - o PCMP real está no
        produto/lot_group e é actualizado pelo mh_stock_valuation.
        """
        self.ensure_one()

        for output_line in self.output_line_ids:
            if not output_line.stock_move_id:
                continue

            move = output_line.stock_move_id
            product = move.product_id

            # Buscar PCMP do lot_group ou produto
            if move.lot_group_id:
                pcmp = move.lot_group_id.pcmp
            else:
                pcmp = product.with_company(self.company_id).pcmp

            output_line.pcmp_calculated = pcmp

        _logger.info(f"PCMP actualizado nas output lines de {self.name}")
