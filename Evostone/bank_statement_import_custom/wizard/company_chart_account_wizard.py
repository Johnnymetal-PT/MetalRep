from odoo import models, fields, api
from odoo.exceptions import UserError


class CompanyChartAccountWizard(models.TransientModel):
    _name = 'company.chart.account.wizard'
    _description = 'Wizard para Adicionar Contas ao Plano'

    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        required=True,
        default=lambda self: self.env.context.get('default_company_id') or self.env.company
    )
    
    action_type = fields.Selection([
        ('existing', 'Reutilizar Contas Existentes'),
        ('new', 'Criar Nova Conta')
    ], string='Ação', default='existing', required=True)
    
    # Campos para selecionar contas existentes
    existing_account_ids = fields.Many2many(
        'company.chart.account',
        string='Contas Disponíveis',
        relation='wizard_existing_accounts_rel',
        column1='wizard_id',
        column2='account_id'
    )
    
    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Atualiza domínio para excluir contas já associadas à empresa"""
        if self.company_id:
            # Busca contas que já estão associadas à empresa atual
            current_account_ids = self.company_id.chart_account_ids.ids
            
            # Retorna domínio para excluir contas já associadas
            return {
                'domain': {
                    'existing_account_ids': [
                        ('id', 'not in', current_account_ids)
                    ]
                }
            }
    
    # Campos para criar nova conta
    new_name = fields.Char(
        string='Nome da Conta'
    )
    
    new_prefix = fields.Char(
        string='Prefixo'
    )
    
    new_account_type = fields.Selection(
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
        help='O tipo de conta é usado para relatórios legais específicos do país'
    )
    
    new_reconcile = fields.Boolean(
        string='Permitir Reconciliação',
        help='Marque se esta conta permite correspondência de faturas e pagamentos'
    )
    
    new_currency_id = fields.Many2one(
        'res.currency',
        string='Moeda da Conta',
        help='Força todos os itens de diário nesta conta a ter uma moeda específica'
    )
    
    new_group_id = fields.Many2one(
        'account.group',
        string='Grupo de Contas',
        help='Grupo de contas para categorização e relatórios'
    )
    
    new_tag_ids = fields.Many2many(
        'account.account.tag',
        string='Etiquetas',
        help='Etiquetas opcionais para relatórios personalizados'
    )
    
    new_allowed_journal_ids = fields.Many2many(
        'account.journal',
        string='Diários Permitidos',
        help='Define em quais diários esta conta pode ser usada'
    )
    
    new_non_trade = fields.Boolean(
        string='Não Comercial',
        default=False,
        help='Se marcado, esta conta pertencerá a Contas a Receber/Pagar Não Comerciais'
    )
    
    new_deprecated = fields.Boolean(
        string='Descontinuada',
        default=False,
        help='Marque se a conta está descontinuada'
    )
    
    new_adiantamento = fields.Boolean(
        string='Adiantamento',
        default=False,
        help='Marque se esta conta é usada para adiantamentos a clientes ou fornecedores'
    )
    
    new_partner_limite = fields.Float(
        string='Limite de Parceiro',
        default=0.0
    )
    
    new_country_id = fields.Many2one(
        'res.country',
        string='País'
    )
    
    @api.onchange('new_account_type')
    def _onchange_new_account_type(self):
        """Auto-ativa reconciliação para contas A Receber e A Pagar"""
        if self.new_account_type in ('asset_receivable', 'liability_payable'):
            self.new_reconcile = True
    
    @api.onchange('action_type')
    def _onchange_action_type(self):
        if self.action_type == 'existing':
            self.new_name = False
            self.new_prefix = False
            self.new_account_type = False
            self.new_reconcile = False
            self.new_currency_id = False
            self.new_group_id = False
            self.new_tag_ids = False
            self.new_allowed_journal_ids = False
            self.new_non_trade = False
            self.new_deprecated = False
            self.new_adiantamento = False
            self.new_partner_limite = 0.0
            self.new_country_id = False
        else:  # new
            self.existing_account_ids = False
    
    def action_confirm(self):
        """Confirma a ação selecionada"""
        self.ensure_one()
        
        if self.env.context.get('active_id'):
            company = self.env['res.company'].browse(self.env.context.get('active_id'))
        else:
            company = self.company_id
            
        if self.action_type == 'existing':
            # Associa contas existentes à empresa (reutilização real)
            if not self.existing_account_ids:
                raise UserError('Por favor, selecione pelo menos uma conta para reutilizar.')
            
            # Apenas adiciona as contas selecionadas à empresa (não cria duplicatas)
            company.chart_account_ids = [(4, account.id) for account in self.existing_account_ids]
            
        else:  # new
            # Cria nova conta global
            if not self.new_name or not self.new_prefix:
                raise UserError('Por favor, preencha o nome e o prefixo da nova conta.')
            
            if not self.new_account_type:
                raise UserError('Por favor, selecione o tipo de conta.')
            
            # Verifica se o prefixo já existe globalmente
            existing = self.env['company.chart.account'].search([
                ('prefix', '=', self.new_prefix)
            ])
            
            if existing:
                raise UserError(f'O prefixo {self.new_prefix} já existe. Use "Reutilizar Contas Existentes" para adicionar esta conta à empresa.')
            
            # Auto-ajusta reconcile para tipos específicos
            reconcile = self.new_reconcile
            if self.new_account_type in ('asset_receivable', 'liability_payable'):
                reconcile = True
            
            # Cria a nova conta global e associa à empresa
            new_account = self.env['company.chart.account'].create({
                'name': self.new_name,
                'prefix': self.new_prefix,
                'account_type': self.new_account_type,
                'reconcile': reconcile,
                'currency_id': self.new_currency_id.id if self.new_currency_id else False,
                'group_id': self.new_group_id.id if self.new_group_id else False,
                'tag_ids': [(6, 0, self.new_tag_ids.ids)] if self.new_tag_ids else False,
                'allowed_journal_ids': [(6, 0, self.new_allowed_journal_ids.ids)] if self.new_allowed_journal_ids else False,
                'non_trade': self.new_non_trade,
                'deprecated': self.new_deprecated,
                'adiantamento': self.new_adiantamento,
                'partner_limite': self.new_partner_limite,
                'country_id': self.new_country_id.id if self.new_country_id else False,
            })
            
            # Associa automaticamente à empresa atual
            company.chart_account_ids = [(4, new_account.id)]
        
        return {'type': 'ir.actions.act_window_close'}