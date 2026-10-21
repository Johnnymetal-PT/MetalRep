from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ImportDocumentActions(models.AbstractModel):
    """Mixin: Ações de workflow do documento de importação

    Responsável por todas as ações de botões e transições de estado:
    - Confirmação (draft → in_transit)
    - Recebimento sem custos (in_transit → partial)
    - Recebimento com custos (in_transit → done)
    - Finalização provisória (partial → done)
    - Cancelamento e retorno a draft
    - Visualização de pickings
    - Atualização manual de linhas

    NOTA: O cálculo de PCMP é delegado ao mh_stock_valuation via stock.landed.cost
    """
    _name = 'import.document.actions'
    _description = 'Import Document Actions Mixin'

    def action_confirm(self):
        """Confirmar importação - Em Trânsito"""
        for doc in self:
            if doc.state != 'draft':
                raise UserError(_("Apenas documentos em rascunho podem ser confirmados."))
            if not doc.import_line_ids:
                raise UserError(_("Adicione pelo menos um produto."))
            if not doc.bank_tc_id:
                raise UserError(_("O campo 'Banco TC' é obrigatório!\n\n"
                                  "Por lei, todas as importações devem ter um Termo de Compromisso (TC) "
                                  "aprovado por um banco comercial."))

            # Gerar sequência se ainda estiver como 'New'
            if doc.name == 'New':
                doc.name = self.env['ir.sequence'].next_by_code('import.document') or 'IMP/001'

            doc.state = 'in_transit'

    def action_receive_without_costs(self):
        """
        RECEBER SEM CUSTOS (Entrada Provisória)

        Usado quando: Faturas despachante/frete AINDA não chegaram

        Fluxo:
        1. Garantir stock_move_ids preenchidos
        2. Validar pickings (SVL criado com FOB pelo mh_stock_valuation)
        3. NÃO criar landed cost (custos ainda não disponíveis)
        4. Estado: partial (aguardando custos)
        """
        for doc in self:
            if doc.state != 'in_transit':
                raise UserError(_("Documento deve estar em trânsito."))

            # Garantir que todas as linhas têm stock_move_id preenchido
            _logger.info(f"Verificando stock_move_id em todas as linhas...")
            doc._ensure_stock_move_ids()

            # Validar pickings (SVL criado com FOB pelo mh_stock_valuation)
            doc._create_provisional_stock_entry()

            # reception_date = date_done do último picking validado
            doc.reception_date = doc._get_last_picking_date_done()

            # Recomputar service lines com taxa da reception_date
            doc._compute_service_lines()

            doc.stock_received = True
            doc.state = 'partial'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Recebido Sem Custos'),
                'message': _('Stock recebido com custo FOB. Adicione custos adicionais quando disponíveis.'),
                'type': 'info',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def action_finalize_provisional(self):
        """
        FINALIZAR ENTRADA PROVISÓRIA

        Usado quando: Custos adicionais chegam APÓS entrada provisória

        Fluxo:
        1. Validar que está em estado 'partial'
        2. Validar que há custos adicionais
        3. Distribuir custos nas linhas (para relatórios)
        4. Criar e validar stock.landed.cost
        5. O mh_stock_valuation calcula PCMP automaticamente
        6. NOVO: Criar ajuste de CMV para vendas do período provisório
        7. Estado: done
        """
        for doc in self:
            if doc.state != 'partial':
                raise UserError(_("Documento deve estar em estado 'Recebido Parcialmente'."))

            # Validar que há custos adicionais com landed_cost_ok = True
            valid_services = doc.service_line_ids.filtered(
                lambda l: l.product_id and l.product_id.landed_cost_ok and l.subtotal > 0
            )

            if not valid_services:
                raise UserError(_(
                    "Não há custos adicionais configurados!\n\n"
                    "Adicione serviços com 'Custo Destino' activo antes de finalizar.\n"
                    "Verifique se os produtos de serviço têm o campo 'landed_cost_ok' marcado."
                ))

            # Distribuir custos nas linhas (para relatórios)
            doc._distribute_costs()

            # Criar e validar landed cost
            # O mh_stock_valuation._update_pcmp_prices() é chamado em button_validate()
            landed_cost = doc._create_landed_cost()
            if landed_cost:
                landed_cost.compute_landed_cost()
                landed_cost.button_validate()
                _logger.info(f"Landed Cost {landed_cost.name} validado - PCMP actualizado automaticamente")

            # NOVO: Criar ajuste de CMV para vendas do período provisório
            # Seguindo IAS 2 / NCRF 18: ajustar CMV das vendas que saíram com custo provisório
            cmv_result = doc._create_cmv_adjustment()
            if cmv_result:
                _logger.info(
                    f"Ajuste CMV criado: {cmv_result['total_adjustment']:.2f} "
                    f"para {len(cmv_result['adjustments'])} produtos"
                )

            doc.pcmp_adjusted = True
            doc.pcmp_calculation_date = fields.Datetime.now()
            doc.state = 'done'

        # Preparar mensagem de notificação
        message = _('Landed cost validado. PCMP actualizado automaticamente.')
        if self.total_cmv_adjustment:
            message += _('\n\nAjuste CMV: %s (vendas no período provisório)') % (
                '{:,.2f}'.format(self.total_cmv_adjustment)
            )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Custos Definitivos Aplicados'),
                'message': message,
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def action_receive_with_costs(self):
        """
        RECEBER COM CUSTOS (Entrada Definitiva)

        Usado quando: Faturas despachante/frete JÁ estão disponíveis

        Fluxo:
        1. Validar custos adicionais existem
        2. Garantir stock_move_ids preenchidos
        3. Validar pickings (SVL criado com FOB pelo mh_stock_valuation)
        4. Distribuir custos nas linhas (para relatórios)
        5. Criar e validar stock.landed.cost
        6. O mh_stock_valuation calcula PCMP automaticamente
        7. Estado: done (finalizado)
        """
        for doc in self:
            if doc.state != 'in_transit':
                raise UserError(_("Documento deve estar em trânsito."))

            # Validar que há custos adicionais com landed_cost_ok = True
            valid_services = doc.service_line_ids.filtered(
                lambda l: l.product_id and l.product_id.landed_cost_ok and l.subtotal > 0
            )

            if not valid_services:
                raise UserError(_(
                    "Não há custos adicionais configurados!\n\n"
                    "Para receber COM custos, adicione serviços com 'Custo Destino' activo.\n"
                    "Verifique se os produtos de serviço têm o campo 'landed_cost_ok' marcado.\n\n"
                    "Se não tem custos adicionais, use 'Receber Sem Custos'."
                ))

            # Garantir que todas as linhas têm stock_move_id preenchido
            _logger.info(f"Verificando stock_move_id em todas as linhas...")
            doc._ensure_stock_move_ids()

            # Validar pickings (SVL criado com FOB pelo mh_stock_valuation)
            doc._create_definitive_stock_entry()

            # reception_date = date_done do último picking validado
            doc.reception_date = doc._get_last_picking_date_done()

            # Recomputar service lines com taxa da reception_date
            doc._compute_service_lines()

            # Distribuir custos nas linhas (para relatórios)
            doc._distribute_costs()

            # Criar e validar landed cost
            # O mh_stock_valuation._update_pcmp_prices() é chamado em button_validate()
            landed_cost = doc._create_landed_cost()
            if landed_cost:
                landed_cost.compute_landed_cost()
                landed_cost.button_validate()
                _logger.info(f"Landed Cost {landed_cost.name} validado - PCMP actualizado automaticamente")

            doc.stock_received = True
            doc.pcmp_adjusted = True
            doc.pcmp_calculation_date = fields.Datetime.now()
            doc.state = 'done'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Recebido Com Custos'),
                'message': _('Stock recebido e PCMP calculado com custos adicionais via Landed Cost.'),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def action_cancel(self):
        """Cancelar importação"""
        for doc in self:
            if doc.state == 'done':
                raise UserError(_("Não pode cancelar importação finalizada."))
            doc.state = 'cancelled'

    def action_draft(self):
        """Voltar a rascunho"""
        for doc in self:
            if doc.state not in ('cancelled',):
                raise UserError(_("Apenas documentos cancelados podem voltar a rascunho."))
            doc.state = 'draft'

    def action_view_pickings(self):
        """Abrir pickings de entrada associados"""
        self.ensure_one()

        if not self.picking_ids:
            raise UserError(_("Nenhum picking associado a este documento de importação."))

        # Se só tem um picking, abrir form view
        if len(self.picking_ids) == 1:
            return {
                'name': _('Picking - %s') % self.name,
                'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'view_mode': 'form',
                'res_id': self.picking_ids.id,
                'context': {'create': False}
            }

        # Múltiplos pickings, abrir list view
        return {
            'name': _('Pickings - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.picking_ids.ids)],
            'context': {'create': False}
        }

    def action_refresh_lines(self):
        """
        Ação manual para forçar atualização das linhas.
        Útil quando pickings foram modificados e usuário quer sincronizar imediatamente.
        """
        self.ensure_one()

        if self.state not in ['draft', 'in_transit']:
            raise UserError(_(
                "Só pode atualizar linhas em estado Rascunho ou Em Trânsito.\n\n"
                "Após receber mercadoria, as linhas ficam congeladas."
            ))

        if self.stock_received:
            raise UserError(_(
                "Stock já foi recebido!\n\n"
                "Não é possível atualizar linhas após entrada de stock."
            ))

        if any(line.landed_cost > 0 for line in self.import_line_ids):
            raise UserError(_(
                "Já existem custos distribuídos!\n\n"
                "Não é possível atualizar linhas após distribuição de custos."
            ))

        # Forçar recálculo
        self.with_context(force_compute=True)._compute_import_lines()

        # Contar linhas criadas
        line_count = len(self.import_line_ids)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Linhas Atualizadas'),
                'message': _('%s linhas sincronizadas com os pickings atuais.') % line_count,
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
