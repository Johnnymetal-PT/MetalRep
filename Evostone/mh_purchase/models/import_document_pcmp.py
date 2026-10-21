# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)



class ImportDocumentPCMP(models.AbstractModel):
    """Mixin: Distribuição de custos e criação de Landed Cost

    Responsável por:
    - Distribuição de custos adicionais nas linhas (para relatórios)
    - Criação de stock.landed.cost seguindo padrão Odoo 18

    NOTA: O cálculo real de PCMP é feito pelo mh_stock_valuation
    via stock.landed.cost.button_validate() → _update_pcmp_prices()
    """
    _name = 'import.document.pcmp'
    _description = 'Import Document Landed Costs Mixin'

    def _distribute_costs(self):
        """
        Distribui custos adicionais espelhando a lógica do stock.landed.cost.

        Usa o mesmo cálculo que o compute_landed_cost() do Odoo:
        - by_quantity: proporcional à quantidade
        - by_weight: proporcional ao peso (para pedra: peso = qty m²)
        - by_volume: proporcional ao volume (para pedra: volume = qty m²)
        - by_current_cost_price: proporcional ao valor (subtotal)
        - equal: divisão igual

        IMPORTANTE: Usa service_line_ids.subtotal (já convertidos e SEM impostos)
        para garantir consistência com o Landed Cost (que usa price_subtotal).
        """
        self.ensure_one()

        if not self.total_product_cost:
            raise UserError(_("Valor total dos produtos não pode ser zero."))

        # Validação de quantidades
        for line in self.import_line_ids:
            if line.quantity <= 0:
                raise ValidationError(_(
                    "Linha %(product)s: quantidade deve ser maior que zero!\n"
                    "Quantidade atual: %(qty)s",
                    product=line.product_id.name,
                    qty=line.quantity
                ))

        # Pré-calcular totais (espelha get_valuation_lines + compute_landed_cost)
        total_qty = 0
        total_weight = 0
        total_volume = 0
        total_cost = 0
        total_line = len(self.import_line_ids)
        line_data = {}

        for line in self.import_line_ids:
            product_form = line.product_id.product_form
            if product_form and product_form != 'none':
                weight = line.quantity
                volume = line.quantity
            else:
                weight = line.product_id.weight * line.quantity
                volume = line.product_id.volume * line.quantity

            line_data[line.id] = {
                'quantity': line.quantity,
                'weight': weight,
                'volume': volume,
                'former_cost': line.subtotal,
            }
            total_qty += line.quantity
            total_weight += weight
            total_volume += volume
            total_cost += line.subtotal

        # Reset landed_cost nas linhas
        for line in self.import_line_ids:
            line.landed_cost = 0

        # Distribuir cada serviço separadamente (espelha LC por cost_line)
        total_service = 0
        for service in self.service_line_ids:
            if service.subtotal <= 0:
                continue

            total_service += service.subtotal
            split_method = getattr(service.product_id, 'split_method_landed_cost', False) or 'by_current_cost_price'

            for line in self.import_line_ids:
                data = line_data[line.id]

                if split_method == 'by_quantity' and total_qty:
                    value = (service.subtotal / total_qty) * data['quantity']
                elif split_method == 'by_weight' and total_weight:
                    value = (service.subtotal / total_weight) * data['weight']
                elif split_method == 'by_volume' and total_volume:
                    value = (service.subtotal / total_volume) * data['volume']
                elif split_method == 'by_current_cost_price' and total_cost:
                    value = (service.subtotal / total_cost) * data['former_cost']
                else:
                    value = service.subtotal / total_line if total_line else 0

                line.landed_cost += value

        # Calcular custo unitário final
        for line in self.import_line_ids:
            line.final_unit_cost = (line.subtotal + line.landed_cost) / line.quantity

            # PCMP calculado: baseado na qty recebida (pode diferir da qty encomendada)
            qty_received = line.quantity_received or line.quantity
            subtotal_received = qty_received * line.unit_price_validated
            line.pcmp_calculated = (subtotal_received + line.landed_cost) / qty_received if qty_received else line.final_unit_cost

        _logger.info(f"Custos distribuídos: {total_service:,.2f} sobre {len(self.import_line_ids)} linhas")

    def _create_landed_cost(self):
        """
        Cria stock.landed.cost seguindo padrão Odoo 18.
        Similar a account.move.button_create_landed_costs()

        O stock.landed.cost distribuirá os custos e o mh_stock_valuation
        fará o cálculo de PCMP via button_validate() → _update_pcmp_prices()
        """
        self.ensure_one()

        # 1. Buscar pickings validados (state='done')
        product_orders = self.purchase_order_ids.filtered(
            lambda po: po.is_product_type
        )
        pickings = product_orders.mapped('picking_ids').filtered(
            lambda p: p.state == 'done' and p.picking_type_code == 'incoming'
        )

        if not pickings:
            raise UserError(_("Nenhum picking validado para aplicar custos!"))

        # 2. Criar linhas de custo
        cost_lines = []

        # 2.1 De POs de serviço (frete, despachante, etc.)
        service_pos = self.purchase_order_ids.filtered(
            lambda po: not po.is_product_type
        )
        for po in service_pos:
            for line in po.order_line:
                # Só incluir produtos com landed_cost_ok = True
                if line.product_id and line.product_id.landed_cost_ok and line.price_subtotal > 0:
                    # Converter para moeda da empresa
                    # reception_date é Datetime, extrair Date para conversão
                    convert_date = self.reception_date.date() if self.reception_date else fields.Date.today()
                    price = po.currency_id._convert(
                        line.price_subtotal,
                        self.company_id.currency_id,
                        self.company_id,
                        convert_date
                    )

                    # Obter conta contabilística
                    account = (
                        line.product_id.property_account_expense_id or
                        line.product_id.categ_id.property_account_expense_categ_id or
                        self.company_id.property_stock_account_input_categ_id
                    )

                    cost_lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'name': f"{po.name}: {line.name}",
                        'price_unit': price,
                        'split_method': getattr(line.product_id, 'split_method_landed_cost', False) or 'by_current_cost_price',
                        'account_id': account.id if account else False,
                    }))

        # 2.2 De serviços embebidos nas POs de mercadoria
        embedded_services = self.service_line_ids.filtered(
            lambda l: not l.is_from_service_po and l.subtotal > 0 and l.product_id and l.product_id.landed_cost_ok
        )
        for service in embedded_services:
            # Obter conta contabilística
            if service.product_id:
                account = (
                    service.product_id.property_account_expense_id or
                    service.product_id.categ_id.property_account_expense_categ_id or
                    self.company_id.property_stock_account_input_categ_id
                )
            else:
                account = self.company_id.property_stock_account_input_categ_id

            cost_lines.append((0, 0, {
                'product_id': service.product_id.id if service.product_id else False,
                'name': service.description or (service.product_id.name if service.product_id else 'Serviço'),
                'price_unit': service.subtotal,  # Já em moeda empresa
                'split_method': getattr(service.product_id, 'split_method_landed_cost', False) or 'by_current_cost_price',
                'account_id': account.id if account else False,
            }))

        if not cost_lines:
            _logger.info(f"Documento {self.name}: Sem custos adicionais para distribuir")
            return False

        # 3. Criar landed cost
        # reception_date é Datetime, extrair Date para o landed cost
        lc_date = self.reception_date.date() if self.reception_date else fields.Date.today()
        landed_cost = self.env['stock.landed.cost'].create({
            'date': lc_date,
            'picking_ids': [(6, 0, pickings.ids)],
            'cost_lines': cost_lines,
        })

        self.landed_cost_id = landed_cost.id
        _logger.info(f"Landed Cost {landed_cost.name} criado para {self.name}")

        return landed_cost

    def _calculate_provisional_sales(self):
        """
        Calcula quantidades vendidas durante o período provisório,
        filtradas por lot_group_id para precisão.

        Obtém lot_group_id pela cadeia segura:
        import_document → picking_ids → move_ids → stock_valuation_layer_ids → lot_group_id

        Retorna dicionário keyed por (product_id, lot_group_id):
        {(pid, lg_id): {
            'qty': float,
            'move_ids': [int],
            'lot_group_id': int or False,
            'product_id': int,
        }}
        """
        self.ensure_one()

        if not self.stock_received:
            _logger.info(f"Doc {self.name}: Sem recepção provisória, sem vendas a ajustar")
            return {}

        if not self.import_line_ids:
            return {}

        # 1. Obter SVLs de entrada pelos pickings DESTA importação
        entry_svls = self.picking_ids.mapped('move_ids.stock_valuation_layer_ids').filtered(
            lambda svl: svl.quantity > 0
        )

        # Coleccionar TODOS os (product_id, lot_group_id) das entradas
        entry_keys = set()
        for svl in entry_svls:
            pid = svl.product_id.id
            lg_id = svl.lot_group_id.id if svl.lot_group_id else False
            entry_keys.add((pid, lg_id))

        SVL = self.env['stock.valuation.layer'].sudo()
        sales_data = {}

        for pid, lg_id in entry_keys:
            # 2. Buscar SVLs de SAÍDA com mesmo product + lot_group
            out_domain = [
                ('product_id', '=', pid),
                ('company_id', '=', self.company_id.id),
                ('quantity', '<', 0),
                ('stock_move_id', '!=', False),
                ('lot_group_id', '=', lg_id),
            ]
            if self.reception_date:
                out_domain.append(('create_date', '>=', self.reception_date))

            out_svls = SVL.search(out_domain)

            if not out_svls:
                continue

            # 3. Descontar RETURNS no mesmo período e lot_group
            ret_domain = [
                ('product_id', '=', pid),
                ('company_id', '=', self.company_id.id),
                ('quantity', '>', 0),
                ('stock_move_id', '!=', False),
                ('lot_group_id', '=', lg_id),
            ]
            if self.reception_date:
                ret_domain.append(('create_date', '>=', self.reception_date))

            ret_svls = SVL.search(ret_domain)
            entry_move_ids = self.picking_ids.mapped('move_ids').ids
            ret_svls = ret_svls.filtered(lambda s: s.stock_move_id.id not in entry_move_ids)
            total_ret = sum(ret_svls.mapped('quantity'))

            # 4. Agrupar saídas por conta de destino (tipo de saída)
            # Cada tipo (venda, quebra, etc.) gera um ajuste separado
            by_account = {}
            for svl in out_svls:
                # Determinar conta de destino a partir do account.move do SVL
                dest_account = False
                if svl.account_move_id:
                    for aml in svl.account_move_id.line_ids:
                        if aml.debit > 0 and aml.account_id.code != '223':
                            dest_account = aml.account_id
                            break
                if not dest_account:
                    # Fallback: conta de custo do produto
                    dest_account = (
                        svl.product_id.categ_id.property_account_expense_categ_id or
                        svl.product_id.property_account_expense_id
                    )
                acc_id = dest_account.id if dest_account else False
                if acc_id not in by_account:
                    by_account[acc_id] = {
                        'qty': 0, 'svls': SVL, 'account': dest_account,
                    }
                by_account[acc_id]['qty'] += abs(svl.quantity)
                by_account[acc_id]['svls'] |= svl

            # Distribuir returns proporcionalmente entre os tipos
            total_out = sum(d['qty'] for d in by_account.values())
            for acc_id, data in by_account.items():
                if total_out > 0 and total_ret > 0:
                    ret_share = total_ret * (data['qty'] / total_out)
                else:
                    ret_share = 0
                net_qty = max(data['qty'] - ret_share, 0)

                if net_qty <= 0:
                    continue

                # Chave: (product_id, lot_group_id, account_id)
                key = (pid, lg_id, acc_id)
                sales_data[key] = {
                    'qty': net_qty,
                    'move_ids': data['svls'].mapped('stock_move_id').ids,
                    'lot_group_id': lg_id,
                    'product_id': pid,
                    'dest_account_id': acc_id,
                    'dest_account': data['account'],
                    'out_svls': data['svls'],
                }

                acc_name = data['account'].code if data['account'] else 'N/A'
                _logger.info(
                    f"Doc {self.name}: Produto {pid}, lg={lg_id}, conta={acc_name}: "
                    f"saidas={data['qty']:.2f}, ret_share={ret_share:.2f}, "
                    f"liquido={net_qty:.2f} un"
                )

        _logger.info(f"Doc {self.name}: Vendas provisórias: {list(sales_data.keys())}")
        return sales_data

    def _get_line_lot_group_id(self, line):
        """
        Obtém lot_group_id de uma import_line via picking → move → SVL.
        Usa lot_name da linha para encontrar o lot_group correcto.
        """
        if not line.base_lot_name:
            return False

        LotGroup = self.env['base.lot.group'].sudo()
        lg = LotGroup.search([
            ('base_lot_name', '=', line.base_lot_name),
            ('product_id', '=', line.product_id.id),
            ('company_id', '=', self.company_id.id),
        ], limit=1)
        return lg.id if lg else False

    def _create_cmv_adjustment(self):
        """
        Cria ajuste de CMV para vendas realizadas durante período provisório.

        Keyed por (product_id, lot_group_id) para suportar múltiplos
        lot_groups do mesmo produto no mesmo import document.

        IAS 2 / NCRF 18: O custo deve ser atribuído ao período em que ocorre
        """
        self.ensure_one()

        # 1. Calcular vendas durante período provisório (keyed por (pid, lg_id))
        sales_data = self._calculate_provisional_sales()

        if not sales_data:
            _logger.info(f"Doc {self.name}: Sem vendas no período provisório - sem ajuste necessário")
            return False

        total_adjustment = 0
        adjustments = []
        svl_created = self.env['stock.valuation.layer']

        # 2. Calcular ajuste para cada import_line, agrupado por tipo de saída
        for line in self.import_line_ids:
            pid = line.product_id.id
            product = line.product_id
            lot_group_id = self._get_line_lot_group_id(line)

            # PCMP provisório = preço FOB (taxa da data de validação)
            pcmp_provisional = line.unit_price_validated
            # PCMP definitivo = custo final unitário (após landed costs)
            # PCMP definitivo: usar pcmp_calculated (qty real dos SVLs) em vez de final_unit_cost (qty encomendada)
            pcmp_definitive = line.pcmp_calculated or line.final_unit_cost
            # Diferença de custo
            cost_diff = pcmp_definitive - pcmp_provisional

            if abs(cost_diff) < 0.01:
                continue

            # Iterar sobre chaves que pertencem a esta linha (pid, lg_id, acc_id)
            keys_for_line = [k for k in sales_data if k[0] == pid and k[1] == lot_group_id]
            total_qty_sold_line = 0

            for key in keys_for_line:
                data = sales_data[key]
                qty_sold = data['qty']

                # Limitar ao máximo que podia ter sido vendido desta importação
                qty_sold = min(qty_sold, line.quantity - total_qty_sold_line)

                if qty_sold <= 0:
                    continue

                total_qty_sold_line += qty_sold

                adjustment_display = cost_diff * qty_sold
                adjustment_svl = -adjustment_display

                total_adjustment += adjustment_display

                dest_account = data.get('dest_account')
                acc_name = dest_account.code if dest_account else 'N/A'

                adjustments.append({
                    'product_id': product,
                    'qty_sold': qty_sold,
                    'pcmp_provisional': pcmp_provisional,
                    'pcmp_definitive': pcmp_definitive,
                    'cost_diff': cost_diff,
                    'adjustment_display': adjustment_display,
                    'adjustment_svl': adjustment_svl,
                    'lot_group_id': lot_group_id,
                    'dest_account_id': data.get('dest_account_id'),
                    'dest_account': dest_account,
                    'move_ids': data.get('move_ids', []),
                })

                _logger.info(
                    f"  {product.name} (lg={lot_group_id}, conta={acc_name}): {qty_sold:.2f} un × "
                    f"({pcmp_definitive:.2f} - {pcmp_provisional:.2f}) = {adjustment_display:.2f}"
                )

                # Buscar SVL de saída original para linkar
                out_svls = data.get('out_svls')
                out_svl = out_svls[-1:] if out_svls else self.env['stock.valuation.layer']

                # Popular adjusted_unit_cost em cada stock.move OUT afectado
                # (acumula se já tinha ajuste anterior). Usado por _get_price_unit
                # para garantir que devoluções entram ao custo real (não provisório).
                if out_svls:
                    for o_svl in out_svls:
                        out_move = o_svl.stock_move_id
                        if not out_move:
                            continue
                        if out_move.adjusted_unit_cost:
                            out_move.adjusted_unit_cost += cost_diff
                        else:
                            original_uc = abs(o_svl.unit_cost) or (
                                abs(o_svl.value) / abs(o_svl.quantity)
                                if o_svl.quantity else 0.0
                            )
                            out_move.adjusted_unit_cost = original_uc + cost_diff

                # Criar SVL de ajuste (padrão Odoo: qty=0, remaining_qty=0)
                svl_vals = {
                    'product_id': product.id,
                    'company_id': self.company_id.id,
                    'quantity': 0,
                    'remaining_qty': 0,
                    'value': adjustment_svl,
                    'unit_cost': 0,
                    'description': f"Ajuste CMV - {self.name} ({qty_sold:.0f} un × {cost_diff:.2f}) [{acc_name}]",
                    'import_document_id': self.id,
                    'is_pcmp_adjustment': True,
                    'lot_group_id': lot_group_id,
                }

                if out_svl:
                    svl_vals['stock_valuation_layer_id'] = out_svl.id

                svl = self.env['stock.valuation.layer'].sudo().create(svl_vals)
                svl_created |= svl

                _logger.info(f"  SVL criado: {svl.id} (conta={acc_name}, linked to OUT SVL: {out_svl.id if out_svl else 'None'})")

                del sales_data[key]

            # Atualizar linha do import document
            if total_qty_sold_line > 0:
                line.write({
                    'qty_sold_provisional': total_qty_sold_line,
                    'cmv_adjustment': cost_diff * total_qty_sold_line,
                })

        if not adjustments:
            _logger.info(f"Doc {self.name}: Sem ajustes de CMV a realizar")
            return False

        _logger.info(f"Doc {self.name}: Total ajuste CMV = {total_adjustment:.2f}, {len(svl_created)} SVLs criados")

        # 5. Criar lançamentos contabilísticos por tipo de saída
        stock_valuation_account = (
            self.import_line_ids[0].product_id.categ_id.property_stock_valuation_account_id
            if self.import_line_ids else False
        )
        all_moves = self.env['account.move']

        for adj in adjustments:
            svl = svl_created.filtered(
                lambda s: s.description and
                (adj['dest_account'].code if adj.get('dest_account') else 'N/A') in s.description
            )
            if not svl:
                continue
            svl = svl[0]

            dest_account = adj.get('dest_account')
            if not dest_account or not stock_valuation_account:
                # Fallback: usar _validate_accounting_entries standard
                svl._validate_accounting_entries()
                all_moves |= svl.account_move_id
                continue

            abs_value = abs(adj['adjustment_svl'])
            lc_date = self.reception_date.date() if self.reception_date else fields.Date.today()

            move_vals = {
                'journal_id': self.env['account.journal'].search(
                    [('code', '=', 'STJ'), ('company_id', '=', self.company_id.id)], limit=1
                ).id,
                'date': lc_date,
                'ref': f"Ajuste CMV - {self.name} [{dest_account.code}]",
                'line_ids': [
                    (0, 0, {
                        'name': f"Ajuste CMV {self.name} - {adj['product_id'].default_code}",
                        'account_id': dest_account.id,
                        'debit': abs_value,
                        'credit': 0,
                    }),
                    (0, 0, {
                        'name': f"Ajuste CMV {self.name} - {adj['product_id'].default_code}",
                        'account_id': stock_valuation_account.id,
                        'debit': 0,
                        'credit': abs_value,
                    }),
                ],
            }
            am = self.env['account.move'].create(move_vals)
            am.action_post()
            svl.account_move_id = am.id
            all_moves |= am

            _logger.info(
                f"  Account move {am.name}: D {dest_account.code} {abs_value:.2f} / C {stock_valuation_account.code} {abs_value:.2f}"
            )

        if all_moves:
            self.cmv_adjustment_move_id = all_moves[0].id

        self.total_cmv_adjustment = total_adjustment

        # 6. Atualizar sale.order.line afetadas
        self._update_sale_order_lines(adjustments)

        return {
            'total_adjustment': total_adjustment,
            'adjustments': adjustments,
            'svl_ids': svl_created.ids,
        }

    def _update_sale_order_lines(self, adjustments):
        """
        Atualiza sale.order.line com custos reais após finalização.

        Para cada venda feita durante o período provisório:
        1. Guarda valores históricos (antes do ajuste) em campos _hist
        2. Atualiza cost_at_confirmation com o PCMP actual do produto
        3. Adiciona este import ao Many2many (rastreabilidade)
        4. Margens recalculam automaticamente

        Adaptado para Stone Trading:
        - product_form != 'none': usar lot.pcmp ou price_group.pcmp (hierarquia lot group)
        - product_form == 'none': usar product.pcmp
        """
        self.ensure_one()

        # Coleccionar todos os move_ids dos adjustments
        all_move_ids = []
        for adj in adjustments:
            all_move_ids.extend(adj.get('move_ids', []))

        if not all_move_ids:
            return

        StockMove = self.env['stock.move'].sudo()
        moves = StockMove.browse(all_move_ids)
        updated_lines = 0

        # Identificar moves que foram retornados (têm return picking associado)
        returned_move_ids = set()
        for move in moves:
            if move.returned_move_ids:
                returned_move_ids.add(move.id)

        for move in moves:
            if not move.sale_line_id:
                continue

            # Ignorar vendas que foram retornadas (o stock voltou e saiu ao custo correcto)
            if move.id in returned_move_ids:
                _logger.info(f"  Move {move.id}: retornado, SOL não actualizada")
                continue

            sol = move.sale_line_id
            product = sol.product_id

            # Buscar PCMP actual usando hierarquia Stone Trading
            product_form = product.product_form if hasattr(product, 'product_form') else 'none'

            if product_form != 'none' and sol.lot_id:
                # Produto dimensional: hierarquia lot.pcmp → price_group.pcmp
                if hasattr(sol.lot_id, 'pcmp') and sol.lot_id.pcmp > 0:
                    pcmp_actual = sol.lot_id.pcmp
                elif hasattr(sol.lot_id, 'price_group_id') and sol.lot_id.sudo().price_group_id and sol.lot_id.sudo().price_group_id.pcmp > 0:
                    pcmp_actual = sol.lot_id.sudo().price_group_id.pcmp
                else:
                    pcmp_actual = product.pcmp if hasattr(product, 'pcmp') else product.standard_price
            else:
                # Produto simples: usar product.pcmp
                pcmp_actual = product.pcmp if hasattr(product, 'pcmp') else product.standard_price

            # Verificar se o custo mudou
            if abs(sol.cost_at_confirmation - pcmp_actual) < 0.01:
                _logger.info(f"  SOL {sol.id}: custo já está actualizado ({pcmp_actual:.2f})")
                continue

            # 1. Guardar valores históricos (apenas se ainda não tem)
            vals = {}
            if not sol.purchase_price_hist:
                vals['purchase_price_hist'] = sol.purchase_price
                vals['margin_amount_hist'] = sol.margin_amount
                vals['margin_percent_hist'] = sol.margin_percent

            # 2. Atualizar custo com PCMP actual
            vals['cost_at_confirmation'] = pcmp_actual

            # 3. Adicionar este import ao Many2many
            vals['import_document_ids'] = [(4, self.id)]

            sol.write(vals)

            updated_lines += 1
            _logger.info(
                f"  SOL {sol.id} (SO: {sol.order_id.name}): "
                f"custo {sol.purchase_price_hist or sol.purchase_price:.2f} → {pcmp_actual:.2f}"
            )

        _logger.info(f"Doc {self.name}: {updated_lines} sale.order.line(s) atualizadas")
