from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta
from markupsafe import Markup
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # ========== CAMPOS ==========
    # Nota: validity_date é campo nativo do Odoo, não redefinimos

    validity_state = fields.Selection([
        ('valid', 'Válida'),
        ('expiring_soon', 'Expirando'),
        ('expired', 'Expirada'),
    ], string='Estado de Validade',
        compute='_compute_validity_state',
        search='_search_validity_state',
        store=False,
        help='Estado da validade da cotação'
    )

    days_until_expiry = fields.Integer(
        string='Dias até Expirar',
        compute='_compute_validity_state',
        search='_search_days_until_expiry',
        store=False,
        help='Número de dias até a cotação expirar'
    )

    is_expired = fields.Boolean(
        string='Expirada',
        compute='_compute_validity_state',
        search='_search_is_expired',
        store=False,
        help='Indica se a cotação está expirada'
    )

    # ========== MÉTODOS COMPUTED ==========
    @api.depends('validity_date', 'state')
    def _compute_validity_state(self):
        """Calcula o estado de validade baseado na data"""
        today = fields.Date.today()

        for order in self:
            # Apenas calcular para cotações (draft e sent)
            if order.state not in ('draft', 'sent') or not order.validity_date:
                order.validity_state = False
                order.days_until_expiry = 0
                order.is_expired = False
                continue

            # Calcular dias até expiração
            delta = order.validity_date - today
            order.days_until_expiry = delta.days

            # Determinar estado
            if delta.days < 0:
                # Expirada
                order.validity_state = 'expired'
                order.is_expired = True
            elif delta.days <= 7:
                # Expirando em breve (7 dias ou menos)
                order.validity_state = 'expiring_soon'
                order.is_expired = False
            else:
                # Válida
                order.validity_state = 'valid'
                order.is_expired = False

    # ========== MÉTODOS SEARCH ==========
    def _search_validity_state(self, operator, value):
        """
        Traduz busca em validity_state para busca em validity_date.
        Permite filtrar cotações por estado de validade sem armazenar o campo.
        """
        today = fields.Date.today()

        if value == 'expired':
            # Cotações expiradas: validity_date < hoje
            return [
                ('state', 'in', ['draft', 'sent']),
                ('validity_date', '<', today)
            ]

        elif value == 'expiring_soon':
            # Cotações expirando: validity_date entre hoje e 7 dias
            seven_days_later = today + timedelta(days=7)
            return [
                ('state', 'in', ['draft', 'sent']),
                ('validity_date', '>=', today),
                ('validity_date', '<=', seven_days_later)
            ]

        elif value == 'valid':
            # Cotações válidas: validity_date > hoje + 7 dias
            seven_days_later = today + timedelta(days=7)
            return [
                ('state', 'in', ['draft', 'sent']),
                ('validity_date', '>', seven_days_later)
            ]

        # Se valor inválido, retornar domínio vazio
        return []

    def _search_is_expired(self, operator, value):
        """
        Traduz busca em is_expired para busca em validity_date.
        """
        today = fields.Date.today()

        if operator == '=' and value:
            # Buscar cotações expiradas
            return [
                ('state', 'in', ['draft', 'sent']),
                ('validity_date', '<', today)
            ]
        elif operator == '=' and not value:
            # Buscar cotações não expiradas
            return [
                ('state', 'in', ['draft', 'sent']),
                ('validity_date', '>=', today)
            ]
        elif operator == '!=':
            # Inverter lógica para !=
            return self._search_is_expired('=', not value)

        return []

    def _search_days_until_expiry(self, operator, value):
        """
        Traduz busca em days_until_expiry para busca em validity_date.
        Exemplo: days_until_expiry < 5 => validity_date < hoje + 5 dias
        """
        today = fields.Date.today()
        target_date = today + timedelta(days=value)

        # Mapear operadores para validity_date
        operator_map = {
            '<': '<',
            '<=': '<=',
            '>': '>',
            '>=': '>=',
            '=': '=',
            '!=': '!='
        }

        if operator in operator_map:
            return [
                ('state', 'in', ['draft', 'sent']),
                ('validity_date', operator_map[operator], target_date)
            ]

        return []

    # ========== CRON JOB ==========
    @api.model
    def _cron_check_expired_quotations(self):
        """Verifica e processa cotações expiradas (executado diariamente)"""
        today = fields.Date.today()

        # Buscar cotações expiradas
        expired_quotations = self.search([
            ('state', 'in', ['draft', 'sent']),
            ('validity_date', '<', today),
        ])

        if not expired_quotations:
            _logger.info('Nenhuma cotação expirada encontrada')
            return

        _logger.info('Encontradas %s cotação(ões) expirada(s)', len(expired_quotations))

        # Verificar se deve cancelar automaticamente
        auto_cancel = self.env['ir.config_parameter'].sudo().get_param(
            'mh_sale_validity.auto_cancel_expired',
            default='False'
        )

        if auto_cancel == 'True':
            # Cancelar cotações expiradas
            for quotation in expired_quotations:
                try:
                    quotation.action_cancel()
                    quotation.message_post(
                        body=Markup(
                            "❌ <b>Cotação Cancelada Automaticamente</b><br/><br/>"
                            "Motivo: Expiração da validade<br/>"
                            "Data de validade: <b>%s</b>"
                        ) % quotation.validity_date.strftime('%d/%m/%Y'),
                        subject='Cotação Cancelada por Expiração',
                        message_type='notification',
                        subtype_xmlid='mail.mt_note'
                    )
                    _logger.info('Cotação %s cancelada automaticamente', quotation.name)
                except Exception as e:
                    _logger.error('Erro ao cancelar cotação %s: %s', quotation.name, str(e))
        else:
            # Apenas notificar (adicionar nota)
            for quotation in expired_quotations:
                quotation.message_post(
                    body=Markup(
                        "⚠️ <b>Cotação Expirada</b><br/><br/>"
                        "Esta cotação expirou em <b>%s</b><br/>"
                        "Por favor, renove a validade ou cancele a cotação"
                    ) % quotation.validity_date.strftime('%d/%m/%Y'),
                    subject='Cotação Expirada',
                    message_type='notification',
                    subtype_xmlid='mail.mt_note'
                )
            _logger.info('Notificações adicionadas a %s cotação(ões)', len(expired_quotations))
