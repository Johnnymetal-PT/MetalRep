# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    # Flag para ativar/desativar funcionalidade
    auto_create_partner_accounts = fields.Boolean(
        string='Criar Contas Parceiros Automaticamente',
        default=False,
        help='Se ativo, cria automaticamente contas contabilísticas para novos parceiros'
    )

    # Configurações de contas
    partner_account_config_ids = fields.One2many(
        'res.company.partner.account.config',
        'company_id',
        string='Configurações de Contas'
    )


class ResCompanyPartnerAccountConfig(models.Model):
    """Configuração de contas de parceiros"""
    _name = 'res.company.partner.account.config'
    _description = 'Configuração de Conta de Parceiro'
    _order = 'partner_type, sequence'

    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        required=True,
        ondelete='cascade',
        default=lambda self: self.env.company
    )

    sequence = fields.Integer(
        string='Sequência',
        default=10
    )

    name = fields.Char(
        string='Nome',
        required=True,
        help='Nome descritivo da configuração (ex: Clientes Nacionais)'
    )

    partner_type = fields.Selection([
        ('customer', 'Cliente'),
        ('supplier', 'Fornecedor'),
    ], string='Tipo de Parceiro', required=True)

    prefix = fields.Char(
        string='Prefixo',
        required=True,
        help='Prefixo para o código da conta (ex: 411)'
    )

    sequence_digits = fields.Integer(
        string='Dígitos Sequência',
        default=4,
        required=True,
        help='Número de dígitos para a sequência (ex: 4 = 0001 a 9999)'
    )

    account_type = fields.Selection(
        selection=[
            ('asset_receivable', 'A Receber'),
            ('asset_cash', 'Banco e Caixa'),
            ('asset_current', 'Ativo Corrente'),
            ('asset_non_current', 'Ativo Não Corrente'),
            ('asset_prepayments', 'Pagamentos Antecipados'),
            ('asset_fixed', 'Ativo Fixo'),
            ('liability_payable', 'A Pagar'),
            ('liability_credit_card', 'Cartão de Crédito'),
            ('liability_current', 'Passivo Corrente'),
            ('liability_non_current', 'Passivo Não Corrente'),
            ('equity', 'Capital Próprio'),
            ('equity_unaffected', 'Lucros Retidos'),
            ('income', 'Receita'),
            ('income_other', 'Outra Receita'),
            ('expense', 'Despesa'),
            ('expense_depreciation', 'Depreciação'),
            ('expense_direct_cost', 'Custo Direto'),
            ('off_balance', 'Extrapatrimonial'),
        ],
        string='Tipo de Conta',
        required=True,
        default='asset_receivable',
        help='Tipo da conta contabilística a criar'
    )

    # Distinguir nacional/estrangeiro
    distinguish_nationality = fields.Boolean(
        string='Distinguir Nacional/Estrangeiro',
        default=False,
        help='Se ativo, usa prefixos diferentes para parceiros nacionais e estrangeiros'
    )

    national_prefix = fields.Char(
        string='Prefixo Nacional',
        help='Prefixo para parceiros nacionais (ex: 4111)'
    )

    foreign_prefix = fields.Char(
        string='Prefixo Estrangeiro',
        help='Prefixo para parceiros estrangeiros (ex: 4112)'
    )

    active = fields.Boolean(
        string='Ativo',
        default=True
    )

    _sql_constraints = [
        ('unique_config_per_company_type',
         'unique(company_id, partner_type)',
         'Já existe uma configuração para este tipo de parceiro nesta empresa!')
    ]

    @api.onchange('partner_type')
    def _onchange_partner_type(self):
        """Define valores padrão baseado no tipo de parceiro"""
        if self.partner_type == 'customer':
            self.account_type = 'asset_receivable'
            if not self.prefix:
                self.prefix = '411'
            if not self.name:
                self.name = 'Clientes'
        elif self.partner_type == 'supplier':
            self.account_type = 'liability_payable'
            if not self.prefix:
                self.prefix = '421'
            if not self.name:
                self.name = 'Fornecedores'

    def get_prefix_for_partner(self, partner):
        """Retorna o prefixo correto baseado na nacionalidade do parceiro"""
        self.ensure_one()
        if not self.distinguish_nationality:
            return self.prefix

        # Verificar se parceiro é estrangeiro
        company_country = self.company_id.country_id
        partner_country = partner.country_id

        if partner_country and company_country and partner_country != company_country:
            return self.foreign_prefix or self.prefix
        else:
            return self.national_prefix or self.prefix
