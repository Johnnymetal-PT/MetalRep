from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class CompanyChartAccount(models.Model):
    _name = 'company.chart.account'
    _description = 'Plano de Contas Global'
    _rec_name = 'display_name'
    _order = 'prefix, name'

    name = fields.Char(
        string='Nome da Conta',
        required=True,
        help='Nome descritivo da conta contábil'
    )
    
    prefix = fields.Char(
        string='Prefixo',
        required=True,
        help='Prefixo único da conta contábil'
    )
    
    # Campo account_type replicado do account.account
    account_type = fields.Selection(
        selection=[
            ('asset_receivable', 'A Receber'),
            ('asset_cash', 'Banco e Caixa'),
            ('asset_current', 'Ativos Circulantes'),
            ('asset_non_current', 'Ativos Não Circulantes'),
            ('asset_prepayments', 'Pagamentos Antecipados'),
            ('asset_fixed', 'Ativos Fixos'),
            ('liability_payable', 'A Pagar'),
            ('liability_credit_card', 'Cartão de Crédito'),
            ('liability_current', 'Passivos Circulantes'),
            ('liability_non_current', 'Passivos Não Circulantes'),
            ('equity', 'Patrimônio'),
            ('equity_unaffected', 'Resultados do Exercício'),
            ('income', 'Receitas'),
            ('income_other', 'Outras Receitas'),
            ('expense', 'Despesas'),
            ('expense_depreciation', 'Depreciação'),
            ('expense_direct_cost', 'Custo da Receita'),
            ('off_balance', 'Contas Extrapatrimoniais'),
        ],
        string='Tipo de Conta',
        required=True,
        help='O tipo de conta é usado para relatórios legais específicos do país e define as regras para fechamento do ano fiscal.'
    )
    
    # Campo reconcile replicado do account.account
    reconcile = fields.Boolean(
        string='Permitir Reconciliação',
        help='Marque esta caixa se esta conta permite correspondência de faturas e pagamentos de itens de diário.'
    )
    
    # Campo currency_id replicado do account.account
    currency_id = fields.Many2one(
        'res.currency',
        string='Moeda da Conta',
        help='Força todos os itens de diário nesta conta a ter uma moeda específica (ex: diários bancários). Se nenhuma moeda for definida, os lançamentos podem usar qualquer moeda.'
    )
    
    # Campo group_id replicado do account.account
    # NOTA: Campo com computed pode causar problemas em views editáveis
    # Implementar com cuidado se necessário
    group_id = fields.Many2one(
        'account.group',
        string='Grupo de Contas',
        help='Grupo de contas para categorização e relatórios',
        ondelete='restrict'
    )
    
    # Campo tag_ids replicado do account.account
    tag_ids = fields.Many2many(
        comodel_name='account.account.tag',
        relation='company_chart_account_tag_rel',
        column1='account_id',
        column2='tag_id',
        string='Etiquetas',
        help='Etiquetas opcionais para relatórios personalizados',
        ondelete='restrict'
    )
    
    # Campo allowed_journal_ids replicado do account.account
    allowed_journal_ids = fields.Many2many(
        'account.journal',
        relation='company_chart_account_journal_rel',
        column1='account_id',
        column2='journal_id',
        string='Diários Permitidos',
        help='Define em quais diários esta conta pode ser usada. Se vazio, pode ser usada em todos os diários.'
    )
    
    # Campo non_trade replicado do account.account
    non_trade = fields.Boolean(
        string='Não Comercial',
        default=False,
        help='Se marcado, esta conta pertencerá a Contas a Receber/Pagar Não Comerciais em relatórios e filtros.\n'
             'Se não, esta conta pertencerá a Contas a Receber/Pagar Comerciais em relatórios e filtros.'
    )
    
    # Campo deprecated replicado do account.account
    deprecated = fields.Boolean(
        string='Descontinuada',
        default=False,
        help='Marque esta caixa se a conta está descontinuada e não deve ser mais usada'
    )
    
    adiantamento = fields.Boolean(
        string='Adiantamento',
        default=False,
        help='Marque esta caixa se esta conta é usada para adiantamentos a clientes ou fornecedores'
    )
    
    partner_limite = fields.Float(
        string='Limite de Parceiro',
        default=0.0,
        help='Limite de crédito padrão para parceiros associados a esta conta'
    )
    
    country_id = fields.Many2one(
        'res.country',
        string='País',
        help='País associado a esta conta contábil'
    )
    
    company_ids = fields.Many2many(
        'res.company',
        'company_chart_account_rel',
        'account_id',
        'company_id',
        string='Empresas',
        help='Empresas que utilizam esta conta'
    )
    
    display_name = fields.Char(
        string='Nome Completo',
        compute='_compute_display_name',
        store=True
    )
    
    active = fields.Boolean(
        string='Ativo',
        default=True
    )
    
    @api.depends('prefix', 'name')
    def _compute_display_name(self):
        for record in self:
            if record.prefix and record.name:
                record.display_name = f"[{record.prefix}] {record.name}"
            elif record.name:
                record.display_name = record.name
            else:
                record.display_name = record.prefix or ''
    
    @api.onchange('account_type')
    def _onchange_account_type(self):
        """Auto-ativa reconciliação para contas A Receber e A Pagar"""
        if self.account_type in ('asset_receivable', 'liability_payable'):
            self.reconcile = True
    
    @api.constrains('account_type', 'reconcile')
    def _check_reconcile(self):
        """Valida que contas A Receber e A Pagar devem ter reconciliação ativada"""
        for record in self:
            if record.account_type in ('asset_receivable', 'liability_payable') and not record.reconcile:
                raise ValidationError(
                    _('Contas do tipo "A Receber" ou "A Pagar" devem ter a reconciliação ativada.')
                )
    
    _sql_constraints = [
        ('prefix_unique', 'unique(prefix)', 'O prefixo da conta deve ser único!'),
    ]
    
    @api.model
    def _init_advance_accounts(self):
        """
        Método de inicialização para garantir que contas 419 e 429
        estejam sempre marcadas como adiantamento
        """
        advance_accounts = self.search([('prefix', 'in', ['419', '429'])])
        if advance_accounts:
            for account in advance_accounts:
                if not account.adiantamento:
                    account.adiantamento = True
                    _logger.info(f"Conta {account.prefix} marcada como adiantamento")
        return True