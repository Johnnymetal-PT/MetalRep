from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountAccount(models.Model):
    _inherit = 'account.account'
    
    # Campo para vincular a conta ao parceiro que a gerou
    partner_id = fields.Many2one(
        'res.partner',
        string='Parceiro Origem',
        help='Parceiro para o qual esta conta foi criada automaticamente'
    )
    
    # Campo para marcar contas geradas automaticamente
    partner_generated = fields.Boolean(
        string='Gerada para Parceiro',
        default=False,
        help='Indica se esta conta foi criada automaticamente para um parceiro'
    )
    
    is_advance_account = fields.Boolean(
        string='É Conta de Adiantamento',
        default=False,
        help='Marcar se esta conta é usada para adiantamentos de clientes/fornecedores'
    )
    
    advance_type = fields.Selection([
        ('customer', 'Adiantamento Cliente'),
        ('supplier', 'Adiantamento Fornecedor')
    ], string='Tipo de Adiantamento',
       help='Define se é conta para adiantamento de cliente ou fornecedor')
    
    @api.onchange('is_advance_account')
    def _onchange_is_advance_account(self):
        """Quando marcar como conta de adiantamento, definir como reconciliável"""
        if self.is_advance_account:
            self.reconcile = True
            # Definir tipo de adiantamento baseado no tipo de conta
            # 419 (liability_current) = adiantamento de cliente
            # 429 (asset_current) = adiantamento de fornecedor
            if self.account_type == 'liability_current':
                self.advance_type = 'customer'
            elif self.account_type == 'asset_current':
                self.advance_type = 'supplier'
    
    # Removida validação restritiva que estava causando erro na importação
    # Contas de adiantamento podem ter diferentes tipos contábeis dependendo da configuração
    # @api.constrains('is_advance_account', 'account_type', 'advance_type')
    # def _check_advance_account_type(self):
    #     """Validar que conta de adiantamento tem o tipo correto para permitir reconciliação"""
    #     for account in self:
    #         if account.is_advance_account:
    #             # Garantir que está marcada como reconciliável
    #             if not account.reconcile:
    #                 account.reconcile = True
    
    def name_get(self):
        """Override name_get para mostrar apenas o nome quando usado em res.company"""
        result = []
        for account in self:
            # Verifica se deve mostrar apenas o nome
            if self._context.get('show_name_only'):
                result.append((account.id, account.name or ''))
            else:
                # Comportamento padrão - usa o método original
                name = account.name or ''
                if account.code:
                    name = account.code + ' ' + name
                result.append((account.id, name))
        return result
    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Override name_search para buscar apenas por nome quando configurado"""
        if self._context.get('show_name_only'):
            args = args or []
            domain = ['|', ('name', operator, name), ('code', operator, name)]
            accounts = self.search(domain + args, limit=limit)
            return accounts.name_get()
        return super().name_search(name, args, operator, limit)