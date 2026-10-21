from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class ImportDocumentStock(models.AbstractModel):
    """Mixin: Operações de stock e sincronização de movimentos

    Responsável por toda lógica de criação e sincronização de stock:
    - Garantir que linhas têm stock_move_id preenchido
    - Sincronizar linhas com stock.move após validação
    - Criar entradas definitivas de stock (com PCMP)
    - Criar entradas provisórias de stock (sem PCMP)
    - Validação de pickings com contextos corretos
    """
    _name = 'import.document.stock'
    _description = 'Import Document Stock Operations Mixin'

    def _ensure_stock_move_ids(self):
        """
        GARANTIR que todas as linhas têm stock_move_id preenchido (REFATORADO).

        Busca moves via:
        1. purchase_order_line_id.move_ids
        2. pickings das POs (fallback)
        """
        self.ensure_one()

        product_orders = self.purchase_order_ids.filtered(lambda po: po.is_product_type)
        pickings = product_orders.mapped('picking_ids').filtered(
            lambda p: p.state in ['assigned', 'done'] and p.picking_type_code == 'incoming'
        )

        for line in self.import_line_ids:
            if line.stock_move_id:
                _logger.info(f"  ✅ Linha {line.product_id.name} já tem stock_move_id={line.stock_move_id.id}")
                continue

            _logger.warning(f"  ⚠️ Linha {line.product_id.name} SEM stock_move_id, buscando...")

            # Método 1: Via purchase_order_line_id
            if line.purchase_order_line_id:
                moves = line.purchase_order_line_id.move_ids.filtered(
                    lambda m: m.state in ['assigned', 'done']
                )
                if moves:
                    # Pegar o primeiro move disponível
                    line.stock_move_id = moves[0].id
                    _logger.info(f"    ✅ Preenchido via POL: stock_move_id={moves[0].id}")
                    continue

            # Método 2: Buscar no picking por produto
            # Obter IDs de moves já usados para evitar reutilização
            used_move_ids = self.import_line_ids.mapped('stock_move_id').ids

            # Buscar moves diretamente
            moves = pickings.mapped('move_ids').filtered(
                lambda m: m.product_id == line.product_id and
                         m.quantity > 0 and
                         m.id not in used_move_ids and  # Evitar moves já associados
                         (not line.base_lot_name or m.lot_name == line.base_lot_name)  # Match de lot_name se existir
            )

            if moves:
                line.stock_move_id = moves[0].id
                _logger.info(f"    ✅ Preenchido via picking: stock_move_id={moves[0].id}")
            else:
                # Tentar diagnóstico para melhor feedback
                all_moves = pickings.mapped('move_ids').filtered(
                    lambda m: m.product_id == line.product_id
                )
                if not all_moves:
                    error_msg = f"Nenhum movimento encontrado para o produto {line.product_id.name}."
                elif all(m.id in used_move_ids for m in all_moves):
                    error_msg = f"Todos os movimentos de {line.product_id.name} já foram associados a outras linhas."
                else:
                    error_msg = f"Movimento encontrado mas quantidade/lote não corresponde."

                _logger.error(f"    ❌ {error_msg}")
                raise UserError(
                    f"❌ {error_msg}\n\n"
                    f"Produto: {line.product_id.name}\n"
                    f"Quantidade esperada: {line.quantity}\n"
                    f"Lote: {line.base_lot_name if line.base_lot_name else 'Nenhum'}\n\n"
                    f"Verifique se os pickings das POs estão em estado 'assigned' ou 'done'."
                )

    def _sync_import_lines_with_stock_moves(self):
        """
        Sincronizar import lines com stock.move APÓS validação do picking (REFATORADO).

        Agora os lotes EXISTEM nas move_lines e podemos sincronizar:
        - stock_move_id
        - lot_id (via computed)
        - lot_name (via computed)
        - quantity real
        """
        self.ensure_one()

        _logger.info("🔄 Sincronizando import lines com stock.move...")

        for line in self.import_line_ids:
            # Se tem stock_move_id, atualizar quantidade do move
            if line.stock_move_id:
                real_qty = line.stock_move_id.product_uom_qty
                if real_qty != line.quantity:
                    line.quantity = real_qty
                    _logger.info(f"Atualizado: {line.product_id.name} = {real_qty} (base_lot_name: {line.base_lot_name or 'N/A'})")
                continue

            # Se não tem stock_move_id, avisar
            _logger.warning(f"⚠️ Linha {line.product_id.name} sem stock_move_id")

        _logger.info(f"✅ Sincronização completa: quantidades atualizadas")

    def _create_definitive_stock_entry(self):
        """
        Validar pickings originais com PCMP correto (REFATORADO).

        PRÉ-CONDIÇÃO: _ensure_stock_move_ids() já garantiu que TODAS as linhas têm stock_move_id

        Fluxo:
        1. Marcar moves como pertencendo a este import document
        2. Validar pickings (SVL será criado com PCMP correto via _create_in_svl)
        """
        self.ensure_one()

        # Buscar pickings das POs de mercadoria
        product_orders = self.purchase_order_ids.filtered(lambda po: po.is_product_type)
        pickings = product_orders.mapped('picking_ids').filtered(
            lambda p: p.state in ['assigned', 'done'] and p.picking_type_code == 'incoming'
        )

        if not pickings:
            raise UserError("Nenhum picking encontrado para validar.")

        # Marcar todos os moves como pertencendo a este import document
        for line in self.import_line_ids:
            # Acessar move diretamente via stock_move_id
            move = line.stock_move_id

            if not move:
                raise UserError(f"ERRO CRÍTICO: Linha {line.product_id.name} sem move após _ensure_stock_move_ids()!")

            # Marcar move como pertencente a este import document
            # O PCMP será buscado diretamente de import_line.pcmp_calculated no _create_in_svl()
            move.write({
                'import_document_id': self.id,
            })

            _logger.info(f"✅ Move {move.id} marcado: {move.product_id.name} - PCMP={line.pcmp_calculated} (será buscado no _create_in_svl)")

        # Validar pickings que ainda não foram validados
        pickings_to_validate = pickings.filtered(lambda p: p.state != 'done')

        if pickings_to_validate:
            # Garantir que move_ids têm quantity done
            for picking in pickings_to_validate:
                for move_line in picking.move_ids:
                    if not move_line.quantity:
                        raise ValidationError(
                            f"❌ O Picking {picking.name} tem algumas linhas sem Quantidade definitiva {move_line.product_id}.\n\n"
                            f"Por favor, ajuste a picking antes de continuar."
                        )

            # Validar pickings COM CONTEXTO from_import_document=True
            # skip_backorder=True para forçar validação sem wizard
            pickings_to_validate.with_context(
                from_import_document=True,
                skip_backorder=True,
                picking_ids_not_to_backorder=pickings_to_validate.ids,
            ).button_validate()

            _logger.info(f"✅ Pickings validados: {pickings_to_validate.mapped('name')}")
        else:
            _logger.info("Pickings já estavam validados")

    def _create_provisional_stock_entry(self):
        """
        Validar pickings originais com custo FOB (entrada provisória) (REFATORADO).

        PRÉ-CONDIÇÃO: _ensure_stock_move_ids() já garantiu que TODAS as linhas têm stock_move_id

        IMPORTANTE: PCMP NÃO é recalculado nesta fase!
        1. Marca moves como pertencendo a este import document
        2. Valida pickings COM flag disable_pcmp_recalc
        - product.standard_price mantém-se inalterado
        - Vendas usarão PCMP atual (anterior à importação)
        """
        self.ensure_one()

        # Buscar pickings das POs de mercadoria
        product_orders = self.purchase_order_ids.filtered(lambda po: po.is_product_type)
        pickings = product_orders.mapped('picking_ids').filtered(
            lambda p: p.state in ['assigned', 'done'] and p.picking_type_code == 'incoming'
        )

        if not pickings:
            raise UserError("Nenhum picking encontrado para validar.")

        # Marcar todos os moves
        for line in self.import_line_ids:
            # Acessar move diretamente via stock_move_id
            move = line.stock_move_id

            if not move:
                raise UserError(f"ERRO CRÍTICO: Linha {line.product_id.name} sem move após _ensure_stock_move_ids()!")

            # Marcar move como pertencente a este import document
            # Na entrada provisória, usa price_unit padrão (FOB) mas NÃO recalcula PCMP
            move.write({
                'import_document_id': self.id,
            })

            _logger.info(f"✅ Move {move.id} marcado (provisório): {move.product_id.name} - usará price_unit FOB (PCMP não recalculado)")

        # Validar pickings que ainda não foram validados COM flag disable_pcmp_recalc
        pickings_to_validate = pickings.filtered(lambda p: p.state != 'done')

        if pickings_to_validate:
            # Garantir que move_lines têm quantity done
            for picking in pickings_to_validate:                        
                for move_line in picking.move_ids:
                    if not move_line.quantity:
                        raise ValidationError(
                            f"❌ O Picking {picking.name} tem algumas linhas sem Quantidade definitiva {move_line.product_id}.\n\n"
                            f"Por favor, ajuste a picking antes de continuar."
                        )

            # Validar pickings COM CONTEXTO para NÃO recalcular PCMP
            # skip_backorder=True para forçar validação sem wizard
            pickings_to_validate.with_context(
                import_provisional=True,
                disable_pcmp_recalc=True,
                from_import_document=True,
                skip_backorder=True,
                picking_ids_not_to_backorder=pickings_to_validate.ids,
            ).button_validate()

            _logger.info(f"✅ Pickings validados (provisório - PCMP não recalculado): {pickings_to_validate.mapped('name')}")
        else:
            _logger.info("Pickings já estavam validados")
