# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from markupsafe import Markup
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # ========================================
    # CAMPOS DE NUMERAÇÃO (para referência)
    # ========================================

    nr_cliente = fields.Integer(
        string='Nº Cliente',
        readonly=True,
        copy=False,
        help='Número sequencial do cliente (referência)'
    )

    nr_fornecedor = fields.Integer(
        string='Nº Fornecedor',
        readonly=True,
        copy=False,
        help='Número sequencial do fornecedor (referência)'
    )

    skip_account_creation = fields.Boolean(
        string='Sem Conta Individual',
        default=False,
        help='Quando marcado, não cria conta contabilística individual (4111/4211) '
             'nem atribui nr_cliente/nr_fornecedor. Usado para funcionários, '
             'parceiros internos ou casos especiais.',
    )

    skip_customer_account_creation = fields.Boolean(
        string='Sem Conta Individual (Cliente)',
        default=False,
        help='Quando marcado, não cria conta 4111/4112 nem atribui nr_cliente. '
             'Para casos em que o parceiro é trabalhador/fornecedor especial mas não cliente individual.',
    )

    skip_supplier_account_creation = fields.Boolean(
        string='Sem Conta Individual (Fornecedor)',
        default=False,
        help='Quando marcado, não cria conta 4211/4212 nem atribui nr_fornecedor. '
             'Para trabalhadores (usam conta 4622 Remunerações) ou casos especiais.',
    )

    def _should_skip_account(self, partner_type):
        """Verifica se deve saltar criação de conta para o tipo indicado.
        Considera o campo legado skip_account_creation e os campos específicos."""
        self.ensure_one()
        if self.skip_account_creation:
            return True
        if partner_type == 'customer' and self.skip_customer_account_creation:
            return True
        if partner_type == 'supplier' and self.skip_supplier_account_creation:
            return True
        return False

    # ========================================
    # CONSTRAINT PAÍS OBRIGATÓRIO (só para parceiros principais)
    # ========================================

    @api.constrains('country_id', 'parent_id')
    def _check_country_required(self):
        """País é obrigatório apenas para parceiros principais (sem parent_id)"""
        for partner in self:
            # Só validar parceiros principais (não contactos filhos)
            if not partner.parent_id and not partner.country_id:
                raise models.ValidationError(
                    _('O campo País é obrigatório para parceiros principais.')
                )

    # ========================================
    # MÉTODOS DE GERAÇÃO DE CONTAS
    # ========================================

    def _get_account_config(self, partner_type):
        """Obtém a configuração de conta para o tipo de parceiro"""
        company = self.company_id or self.env.company
        config = self.env['res.company.partner.account.config'].search([
            ('company_id', '=', company.id),
            ('partner_type', '=', partner_type),
            ('active', '=', True),
        ], limit=1)
        return config

    def _get_next_sequence_from_accounts(self, prefix, digits):
        """
        Obtém o próximo número sequencial para CONTA baseado nas contas existentes.
        Busca usando ORM do Odoo (compatível com Odoo 18).
        Cada prefixo tem a sua própria sequência independente.

        Args:
            prefix: Prefixo da conta (ex: '4111', '4112', '4211', '4212')
            digits: Número de dígitos da sequência (ex: 4)

        Returns:
            int: Próximo número sequencial para a conta
        """
        company = self.company_id or self.env.company

        # Buscar contas que começam com o prefixo usando ORM (excluir órfãs)
        accounts = self.env['account.account'].search([
            ('code', '=like', prefix + '%'),
            ('company_ids', 'in', company.id),
            ('is_orphan', '=', False),
        ])

        max_number = 0
        for account in accounts:
            code = account.code
            if code and code.startswith(prefix):
                try:
                    sequence_part = code[len(prefix):]
                    number = int(sequence_part)
                    if number > max_number:
                        max_number = number
                except (ValueError, IndexError):
                    continue

        return max_number + 1

    def _get_next_partner_number(self, partner_type):
        """
        Obtém o próximo número sequencial para nr_cliente ou nr_fornecedor.
        Sequência global independente da conta.

        Args:
            partner_type: 'customer' ou 'supplier'

        Returns:
            int: Próximo número sequencial
        """
        field_name = 'nr_cliente' if partner_type == 'customer' else 'nr_fornecedor'

        self.env.cr.execute(f"""
            SELECT COALESCE(MAX({field_name}), 0)
            FROM res_partner
        """)

        max_number = self.env.cr.fetchone()[0]
        return max_number + 1

    def _generate_account_code(self, config, sequence_number):
        """
        Gera o código da conta contabilística
        Formato: PREFIXO + SEQUÊNCIA
        Exemplo: 4111 + 0001 = 41110001
        """
        prefix = config.get_prefix_for_partner(self)
        sequence_str = str(sequence_number).zfill(config.sequence_digits)
        return f"{prefix}{sequence_str}"

    def _create_partner_account(self, partner_type):
        """Cria a conta contabilística para o parceiro"""
        self.ensure_one()

        # Ignorar parceiros com skip (legado ou por tipo)
        if self._should_skip_account(partner_type):
            _logger.info(f"Parceiro {self.name}: skip para {partner_type}, ignorando criação de conta")
            return False

        company = self.company_id or self.env.company

        # Verificar se a funcionalidade está ativa
        if not company.auto_create_partner_accounts:
            return False

        # Obter configuração
        config = self._get_account_config(partner_type)
        if not config:
            _logger.warning(
                f"Nenhuma configuração de {partner_type} para a empresa {company.name}"
            )
            return False

        # Obter o prefixo correto para este parceiro (nacional/estrangeiro)
        prefix = config.get_prefix_for_partner(self)

        # Obter próximo número sequencial global (nr_cliente/nr_fornecedor)
        # Este número é usado tanto para o parceiro como para os dígitos da conta
        next_partner_seq = self._get_next_partner_number(partner_type)

        # Gerar código da conta usando o nr_cliente/nr_fornecedor como dígitos
        account_code = f"{prefix}{str(next_partner_seq).zfill(config.sequence_digits)}"

        # Verificar se a conta já existe
        Account = self.env['account.account']
        existing_account = Account.search([
            ('code', '=', account_code),
            ('company_ids', 'in', company.id),
        ], limit=1)

        if existing_account:
            _logger.warning(f"Conta {account_code} já existe")
            return existing_account

        # Criar a conta
        new_account = Account.create({
            'code': account_code,
            'name': self.name,
            'account_type': config.account_type,
            'company_ids': [(6, 0, [company.id])],
            'reconcile': True,
        })

        _logger.info(f"Conta {account_code} criada para parceiro {self.name}")

        # Atualizar o parceiro
        vals = {}
        if partner_type == 'customer':
            vals['nr_cliente'] = next_partner_seq  # Sequência global
            vals['property_account_receivable_id'] = new_account.id
        else:
            vals['nr_fornecedor'] = next_partner_seq  # Sequência global
            vals['property_account_payable_id'] = new_account.id

        super(ResPartner, self).write(vals)

        return new_account

    def action_confirm_create_accounts(self):
        """Ação chamada pelo wizard de confirmação"""
        self.ensure_one()
        # Só criar conta de cliente se for cliente
        if self.customer_rank > 0 and not self.nr_cliente:
            self._create_partner_account('customer')
        # Só criar conta de fornecedor se for fornecedor
        if self.supplier_rank > 0 and not self.nr_fornecedor:
            self._create_partner_account('supplier')
        return True

    def action_skip_create_accounts(self):
        """Ação para pular a criação de contas"""
        return True

    # ========================================
    # BOTÃO PARA CRIAR CONTA MANUALMENTE
    # ========================================

    can_create_partner_account = fields.Boolean(
        compute='_compute_can_create_partner_account',
        string='Pode Criar Conta'
    )

    @api.depends('customer_rank', 'supplier_rank', 'nr_cliente', 'nr_fornecedor', 'parent_id')
    def _compute_can_create_partner_account(self):
        """Verifica se pode criar conta para este parceiro"""
        for partner in self:
            can_create = False
            # Só para parceiros principais
            if not partner.parent_id:
                # Cliente sem conta
                if partner.customer_rank > 0 and not partner.nr_cliente:
                    can_create = True
                # Fornecedor sem conta
                if partner.supplier_rank > 0 and not partner.nr_fornecedor:
                    can_create = True
            partner.can_create_partner_account = can_create

    def action_open_create_account_wizard(self):
        """Abre o wizard para criar conta contabilística"""
        self.ensure_one()
        return {
            'name': _('Criar Conta de Parceiro'),
            'type': 'ir.actions.act_window',
            'res_model': 'partner.account.confirm.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
            }
        }

    # ========================================
    # CONVERSÕES CLIENTE / FORNECEDOR
    # ========================================

    def action_convert_to_customer(self):
        """Tornar fornecedor também cliente e criar conta contabilística de cliente."""
        self.ensure_one()
        vals = {}
        if self.skip_account_creation:
            vals['skip_account_creation'] = False
        if self.skip_customer_account_creation:
            vals['skip_customer_account_creation'] = False
        if self.customer_rank <= 0:
            vals['customer_rank'] = 1
        if vals:
            self.write(vals)
        if not self.nr_cliente:
            self.ensure_partner_account('customer')
        self.message_post(
            body=Markup(
                "🔄 <b>Conversão para Cliente</b><br/><br/>"
                "O parceiro <b>%s</b> foi convertido para <b>Cliente</b> por <b>%s</b>.<br/>"
                "Nº Cliente: <b>%s</b>"
            ) % (self.name, self.env.user.name, self.nr_cliente or '—'),
            subject=_('Conversão para Cliente'),
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Cliente'),
                'message': _('%s agora também é cliente.') % self.name,
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.client', 'tag': 'soft_reload'},
            }
        }

    def action_convert_to_supplier(self):
        """Tornar cliente também fornecedor e criar conta contabilística de fornecedor."""
        self.ensure_one()
        vals = {}
        if self.skip_account_creation:
            vals['skip_account_creation'] = False
        if self.skip_supplier_account_creation:
            vals['skip_supplier_account_creation'] = False
        if self.supplier_rank <= 0:
            vals['supplier_rank'] = 1
        if vals:
            self.write(vals)
        if not self.nr_fornecedor:
            self.ensure_partner_account('supplier')
        self.message_post(
            body=Markup(
                "🔄 <b>Conversão para Fornecedor</b><br/><br/>"
                "O parceiro <b>%s</b> foi convertido para <b>Fornecedor</b> por <b>%s</b>.<br/>"
                "Nº Fornecedor: <b>%s</b>"
            ) % (self.name, self.env.user.name, self.nr_fornecedor or '—'),
            subject=_('Conversão para Fornecedor'),
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Fornecedor'),
                'message': _('%s agora também é fornecedor.') % self.name,
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.client', 'tag': 'soft_reload'},
            }
        }

    # ========================================
    # MÉTODO PARA CRIAR CONTA (chamado de sale.order, purchase.order, account.payment)
    # ========================================

    def ensure_partner_account(self, partner_type):
        """Garante que o parceiro tem conta contabilística.

        Chamado por:
        - sale.order.action_confirm() → partner_type='customer'
        - purchase.order.button_confirm() → partner_type='supplier'
        - account.payment.action_post() → partner_type conforme tipo

        Args:
            partner_type: 'customer' ou 'supplier'

        Returns:
            account.account ou False
        """
        self.ensure_one()

        # Ignorar contactos filhos e parceiros com skip
        if self.parent_id or self._should_skip_account(partner_type):
            return False

        company = self.company_id or self.env.company
        user = self.env.user

        # Verificar se funcionalidade está ativa
        if not company.auto_create_partner_accounts:
            return False

        # Se utilizador quer confirmação, não criar automaticamente
        if user.ask_create_partner_account:
            return False

        # Verificar se já tem conta
        if partner_type == 'customer' and self.nr_cliente:
            return False
        if partner_type == 'supplier' and self.nr_fornecedor:
            return False

        _logger.info(f"Criando conta de {partner_type} para {self.name}")
        return self._create_partner_account(partner_type)

    # ========================================
    # OVERRIDE CREATE
    # ========================================

    @api.model_create_multi
    def create(self, vals_list):
        """Override create para criar contas automaticamente"""
        partners = super().create(vals_list)

        for partner in partners:
            # Ignorar contactos filhos
            if partner.parent_id:
                continue

            company = partner.company_id or self.env.company
            user = self.env.user

            # Verificar se funcionalidade está ativa
            if not company.auto_create_partner_accounts:
                continue

            # Se utilizador quer confirmação, não criar automaticamente
            if user.ask_create_partner_account:
                continue

            # Criar automaticamente só para o tipo correto (respeitando skip especifico)
            if partner.customer_rank > 0 and not partner._should_skip_account('customer'):
                partner._create_partner_account('customer')
            if partner.supplier_rank > 0 and not partner._should_skip_account('supplier'):
                partner._create_partner_account('supplier')

        return partners
