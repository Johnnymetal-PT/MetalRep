# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_round
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_initial_stock = fields.Boolean(
        string='Stock Inicial',
        compute='_compute_is_initial_stock',
        help="Indica se este é um picking de Stock Inicial.",
    )

    # Campo para definir ponto de partida da sequência (usado em migrações)
    last_serial_sequence = fields.Integer(
        string='Última Sequência Serial',
        default=0,
        help='Para Stock Inicial: define o ponto de partida da sequência.\n'
             'Ao validar, a sequência será actualizada para este valor.\n'
             'Ex: Se definir 1000, a próxima operação usará #1001'
    )

    @api.depends('picking_type_id')
    def _compute_is_initial_stock(self):
        initial_stock_type = self.env.ref(
            'mh_stock_valuation.picking_type_initial_stock',
            raise_if_not_found=False
        )
        for picking in self:
            picking.is_initial_stock = (
                initial_stock_type and picking.picking_type_id.id == initial_stock_type.id
            )

    def button_validate(self):
        """
        Override para processar recepções com split de linhas, grupos de lote e PCMP.

        Sequência:
        1. Split de linhas por units_qty (ANTES do super) - EXCLUIR Stock Inicial
        2. Criar registos PCMP fiscal year para Stock Inicial (ANTES do super)
        3. Actualizar sequência serial se definido em Stock Inicial (ANTES do super)
        4. Chamar super() que cria lotes, SVLs e calcula PCMP
        5. Ajustar PCMP para Stock Inicial (DEPOIS do super)
        6. Associar lotes aos grupos de preço (DEPOIS do super)
        """
        # 0. Validar que lot_name não tem lot_group existente (duplicação)
        for picking in self.filtered(
            lambda p: p.picking_type_code == 'incoming' and not p.sale_id
        ):
            picking._check_duplicate_lot_groups()

        # 1. Split de linhas para recepções (EXCLUIR stock inicial - não faz split)
        for picking in self.filtered(
            lambda p: p.picking_type_code == 'incoming' and not p.is_initial_stock and not p.sale_id
        ):
            picking._split_lines_by_units_qty()

        # 2. Processar pickings de Stock Inicial
        for picking in self.filtered(lambda p: p.is_initial_stock and not p.sale_id):
            picking._create_pcmp_fiscal_year_records()
            # 3. Actualizar sequência se definido (para migrações)
            if picking.last_serial_sequence > 0:
                picking._update_serial_sequence()

        # 3. Chamar super() - isto cria lotes, SVLs e actualiza preços
        res = super().button_validate()

        # 4. Após validação, ajustar PCMP para usar o valor inicial
        for picking in self.filtered(lambda p: p.is_initial_stock and not p.sale_id):
            picking._set_initial_pcmp_prices()

        # 5. Associar lotes aos grupos de preço
        for picking in self.filtered(lambda p: p.picking_type_code == 'incoming' and not p.sale_id):
            picking._associate_lots_to_price_groups()

        return res

    # ========================================
    # VALIDAÇÃO DE LOT GROUPS DUPLICADOS
    # ========================================

    def _check_duplicate_lot_groups(self):
        """Verifica se lot_name dos moves já tem base.lot.group existente.

        Previne importar material para um lot_group que já existe,
        garantindo unicidade (base_lot_name + product_id + company_id).
        Apenas para produtos com product_form != 'none' e lot_name válido.
        """
        self.ensure_one()
        LotGroup = self.env['base.lot.group'].sudo()

        for move in self.move_ids.filtered(
            lambda m: m.lot_name
            and m.product_id.cost_method == 'pcmp'
            and getattr(m.product_id, 'product_form', 'none') != 'none'
        ):
            existing = LotGroup.search([
                ('base_lot_name', '=', move.lot_name),
                ('product_id', '=', move.product_id.id),
                ('company_id', '=', move.company_id.id),
            ], limit=1)

            if existing:
                raise ValidationError(_(
                    "Já existe um grupo de lote '%(lot_name)s' para o produto '%(product)s'!\n\n"
                    "Grupo existente: %(group)s\n"
                    "PCMP actual: %(pcmp).2f\n\n"
                    "Cada lote base deve ser único por produto. "
                    "Verifique o nome do lote ou utilize o grupo existente.",
                    lot_name=move.lot_name,
                    product=move.product_id.display_name,
                    group=existing.display_name,
                    pcmp=existing.pcmp,
                ))

    # ========================================
    # SPLIT DE LINHAS E GERAÇÃO DE LOTES
    # ========================================

    def _split_lines_by_units_qty(self):
        """Divide move lines baseado em units_qty

        Para cada line com units_qty > 1:
        - Cria units_qty linhas
        - Cada linha com quantity / units_qty
        - Gera lot_name com formato #N/CÓDIGO/NOME_BASE

        Para units_qty = 1:
        - Apenas gera lot_name sem dividir
        """
        lines_to_process = self.move_line_ids.filtered(
            lambda l: (
                l.product_id.tracking != 'none' and  # Produto rastreável
                not l.lot_id and  # Não tem lote já atribuído
                hasattr(l, 'units_qty') and  # Tem campo units_qty
                (l.units_qty or 1) >= 1 and  # units_qty maior ou igual a 1
                (not hasattr(l.product_id, 'product_form') or l.product_id.product_form != 'none')  # Produto com forma física
            )
        )

        # Snapshot pré-split: guarda o estado de cada move_line antes da
        # divisão para se poder investigar discrepâncias entre o pretendido
        # e o resultado final. Criação em batch para minimizar I/O ao DB.
        snapshot_vals = [{
            'move_id': line.move_id.id,
            'product_id': line.product_id.id,
            'units_qty': line.units_qty or 1,
            'quantity': line.quantity,
            'length': line.length if hasattr(line, 'length') else 0.0,
            'width': line.width if hasattr(line, 'width') else 0.0,
            'thickness': line.thickness if hasattr(line, 'thickness') else 0.0,
            'lot_name_base': line.move_id.lot_name or '',
        } for line in lines_to_process]
        if snapshot_vals:
            try:
                self.env['stock.move.line.snapshot'].sudo().create(snapshot_vals)
            except Exception as e:
                _logger.warning(
                    "Snapshot pré-split falhou para picking %s: %s",
                    self.name, e,
                )

        for line in lines_to_process:
            units_qty = line.units_qty or 1

            # Nome base do lote (do stock.move)
            base_lot_name = line.move_id.lot_name if line.move_id else ''

            # Código do produto
            product_code = line.product_id.default_code or line.product_id.name

            if units_qty > 1:
                # Caso: Dividir em múltiplas linhas
                uom_rounding = line.product_uom_id.rounding if line.product_uom_id else 0.0001
                qty_per_unit = float_round(line.quantity / units_qty, precision_rounding=uom_rounding)

                # Gerar número de sequência global para primeira unidade
                seq_num_first = self._get_next_serial_number()

                # Criar units_qty - 1 novas linhas (cópias)
                for i in range(1, units_qty):
                    seq_num = self._get_next_serial_number()
                    lot_name = self._generate_lot_name(seq_num, product_code, base_lot_name)
                    line.copy({
                        'quantity': qty_per_unit,
                        'units_qty': 1,
                        'lot_name': lot_name,
                    })

                # Atualizar linha original
                lot_name = self._generate_lot_name(seq_num_first, product_code, base_lot_name)
                line.write({
                    'quantity': qty_per_unit,
                    'units_qty': 1,
                    'lot_name': lot_name,
                })
            else:
                # Caso: Apenas gerar lot_name para unidade única
                seq_num = self._get_next_serial_number()
                lot_name = self._generate_lot_name(seq_num, product_code, base_lot_name)
                line.write({
                    'lot_name': lot_name,
                })

    def _get_next_serial_number(self):
        """Obtém próximo número de série global da sequência

        Returns:
            int: Próximo número sequencial (1, 2, 3, ...)

        Examples:
            >>> _get_next_serial_number()  # sequência retorna "#000001"
            1
        """
        sequence = self.env['ir.sequence'].next_by_code('stock.quant.serial')
        if not sequence:
            return 1

        # Extrair número da sequência (remover # e zeros à esquerda)
        number_str = sequence.replace('#', '').lstrip('0')
        return int(number_str) if number_str else 1

    def _generate_lot_name(self, sequence_number, product_code, base_name):
        """Gera nome de lote no formato #N/CÓDIGO/NOME_BASE

        Args:
            sequence_number (int): Número sequencial global (1, 2, 3...)
            product_code (str): Código do produto (default_code)
            base_name (str): Nome base do lote (lot_name do move)

        Returns:
            str: Nome do lote formatado

        Examples:
            >>> _generate_lot_name(1, "MARM001", "LOTE_ABC")
            "#1/MARM001/LOTE_ABC"
        """
        parts = [f"#{sequence_number}", product_code]

        if base_name:
            parts.append(base_name)

        return "/".join(parts)

    # ========================================
    # ASSOCIAÇÃO DE LOTES A GRUPOS DE PREÇO
    # ========================================

    def _associate_lots_to_price_groups(self):
        """Associa lotes criados aos grupos de preço baseado em dimensões

        Após validação do picking:
        - Para cada lote criado com dimensões
        - Busca ou cria grupo de preço com dimensões idênticas
        - Associa lote ao grupo

        O base.lot.group já foi criado pelo stock_move durante a validação.
        """
        for line in self.move_line_ids:
            # Pular produtos sem forma física
            if hasattr(line.product_id, 'product_form') and line.product_id.product_form == 'none':
                continue

            # Só processar se tem lote
            if not line.lot_id:
                continue

            lot = line.lot_id

            # Se lote já tem grupo de preço, não fazer nada
            if hasattr(lot, 'price_group_id') and lot.sudo().price_group_id:
                continue

            # Se lote não tem campos de dimensões, pular
            if not (hasattr(lot, 'length') and hasattr(lot, 'width') and hasattr(lot, 'thickness')):
                continue

            # PASSO 1: Copiar dimensões e base_lot_name da move_line para o lote
            vals_to_write = {}

            # Copiar dimensões se o lote não tiver
            if not lot.length and not lot.width and not lot.thickness:
                if hasattr(line, 'length') and line.length:
                    vals_to_write['length'] = line.length
                if hasattr(line, 'width') and line.width:
                    vals_to_write['width'] = line.width
                if hasattr(line, 'thickness') and line.thickness:
                    vals_to_write['thickness'] = line.thickness

            # Copiar base_lot_name do move (se lote não tiver)
            if hasattr(lot, 'base_lot_name') and not lot.base_lot_name:
                if line.move_id and line.move_id.lot_name:
                    vals_to_write['base_lot_name'] = line.move_id.lot_name

            # Usar sudo() para escrever mesmo com readonly=True
            if vals_to_write:
                lot.sudo().write(vals_to_write)

            # PASSO 2: Pegar dimensões do lote (agora já preenchidas)
            length = lot.length or 0.0
            width = lot.width or 0.0
            thickness = lot.thickness or 0.0

            # Se todas as dimensões são 0, pular
            if length == 0.0 and width == 0.0 and thickness == 0.0:
                continue

            # PASSO 3: Obter valores para criação do grupo de preço
            peso = line.peso if hasattr(line, 'peso') else 0.0
            price_unit = line.move_id.price_unit or line.product_id.standard_price
            base_lot_name = lot.base_lot_name if hasattr(lot, 'base_lot_name') else ''

            # PASSO 4: Buscar ou criar grupo de preço
            # O lot.price.group.find_or_create_group() também cria base.lot.group se necessário
            PriceGroup = self.env['lot.price.group'].sudo()
            price_group = PriceGroup.find_or_create_group(
                product_id=lot.product_id.id,
                length=length,
                width=width,
                thickness=thickness,
                base_lot_name=base_lot_name,
                final_cost=price_unit,
                pcmp=price_unit,
                company_id=self.company_id.id,
            )

            # PASSO 5: Associar lote ao grupo de preço (sudo para garantir permissões)
            lot.sudo().write({'price_group_id': price_group.id})

    def _log_price_group_associations(self):
        """Log das associações criadas para auditoria

        Registra no chatter do picking quais lotes foram associados a quais grupos,
        incluindo informação do base.lot.group (hierarquia superior).
        """
        associations = []
        for line in self.move_line_ids:
            if line.lot_id and hasattr(line.lot_id, 'price_group_id') and line.lot_id.sudo().price_group_id:
                lot = line.lot_id
                pg = lot.sudo().price_group_id

                # Informação do base group
                base_info = ''
                if pg.base_lot_group_id:
                    base_info = f" (Base: {pg.base_lot_group_id.name}, PCMP: {pg.base_lot_group_id.pcmp:.2f})"

                associations.append(
                    f"  • {lot.name} → {pg.name}{base_info}"
                )

        if associations:
            self.message_post(
                body=f"<b>Lotes associados aos grupos de preço:</b><br/>{'<br/>'.join(associations)}"
            )

    # ========================================
    # STOCK INICIAL - PCMP FISCAL YEAR
    # ========================================

    def _update_serial_sequence(self):
        """
        Actualiza a sequência stock.quant.serial com o valor de last_serial_sequence.

        Usado em Stock Inicial para definir ponto de partida após migração de dados.
        Ex: Se last_serial_sequence = 1000, próximo número gerado será #1001

        Isto permite que ao migrar dados existentes, possamos definir que os
        próximos lotes criados continuem a partir de um número específico.
        """
        self.ensure_one()

        if not self.last_serial_sequence:
            return

        sequence = self.env['ir.sequence'].search([
            ('code', '=', 'stock.quant.serial')
        ], limit=1)

        if sequence:
            # Actualizar number_next para o valor seguinte
            sequence.sudo().write({
                'number_next': self.last_serial_sequence + 1
            })
            _logger.info(
                f"Sequência stock.quant.serial actualizada via Stock Inicial {self.name}: "
                f"próximo número será #{self.last_serial_sequence + 1}"
            )

    def _create_pcmp_fiscal_year_records(self):
        """
        Cria registos mh.pcmp.fiscal.year para cada movimento do picking.

        Para Stock Inicial PCMP, o price_unit do movimento é o PCMP inicial
        e a quantidade é o stock inicial.
        """
        self.ensure_one()
        FiscalYear = self.env['mh.pcmp.fiscal.year'].sudo()

        for move in self.move_ids.filtered(
            lambda m: m.product_id.cost_method == 'pcmp' and m.state != 'cancel'
        ):
            # Obter dados
            product = move.product_id
            fiscal_year = (move.date or fields.Datetime.now()).year
            company = move.company_id
            quantity = move.product_uom_qty
            unit_cost = move.price_unit or product.standard_price

            # Verificar se tem lot_group
            lot_group = None
            if move.lot_name:
                # Criar ou obter lot_group
                lot_group = move._get_or_create_lot_group()
                if lot_group:
                    move.lot_group_id = lot_group

            # Procurar registo existente
            domain = [
                ('product_id', '=', product.id),
                ('fiscal_year', '=', fiscal_year),
                ('company_id', '=', company.id),
            ]
            if lot_group:
                domain.append(('lot_group_id', '=', lot_group.id))
            else:
                domain.append(('lot_group_id', '=', False))

            existing = FiscalYear.search(domain, limit=1)

            if existing:
                # Actualizar valores (somar ao existente)
                existing.write({
                    'initial_stock': existing.initial_stock + quantity,
                    'initial_pcmp': unit_cost,  # Usar o novo custo
                })
            else:
                # Criar novo registo
                FiscalYear.create({
                    'product_id': product.id,
                    'fiscal_year': fiscal_year,
                    'company_id': company.id,
                    'lot_group_id': lot_group.id if lot_group else False,
                    'initial_stock': quantity,
                    'initial_pcmp': unit_cost,
                })

    def _set_initial_pcmp_prices(self):
        """
        Força recálculo do PCMP após Stock Inicial.

        O PCMP é agora um campo computed que calcula automaticamente
        a partir das SVLs e registos do ano fiscal. Este método apenas
        força a invalidação do cache para garantir recálculo.
        """
        self.ensure_one()

        for move in self.move_ids.filtered(
            lambda m: m.product_id.cost_method == 'pcmp' and m.state == 'done'
        ):
            # PCMP é computed - forçar invalidação do cache
            if move.lot_group_id:
                move.lot_group_id.invalidate_recordset(['pcmp'])
            else:
                move.product_id.invalidate_recordset(['pcmp'])
