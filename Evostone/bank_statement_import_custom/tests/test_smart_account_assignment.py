from odoo.tests import common
from odoo.exceptions import ValidationError


class TestSmartAccountAssignment(common.TransactionCase):
    """Testes para verificar atribuição inteligente de contas aos campos padrão"""
    
    def setUp(self):
        super().setUp()
        
        # Get models
        self.Partner = self.env['res.partner']
        self.Company = self.env['res.company']
        self.ChartAccount = self.env['company.chart.account']
        self.Account = self.env['account.account']
        self.Country = self.env['res.country']
        
        # Get countries
        self.mozambique = self.Country.search([('code', '=', 'MZ')], limit=1)
        if not self.mozambique:
            self.mozambique = self.Country.create({
                'name': 'Mozambique',
                'code': 'MZ'
            })
        
        # Set company country
        self.env.company.country_id = self.mozambique
        
        # Clean existing chart configs for test isolation
        self.env.company.chart_account_ids = [(5, 0, 0)]
    
    def test_01_receivable_account_to_standard_field(self):
        """Testa se conta asset_receivable vai para property_account_receivable_id"""
        
        # Create receivable configuration
        receivable_config = self.ChartAccount.create({
            'prefix': '411',
            'name': 'Clientes Nacionais',
            'account_type': 'asset_receivable',
            'reconcile': True,
            'partner_limite': 4,
            'company_ids': [(4, self.env.company.id)]
        })
        
        # Create partner
        partner = self.Partner.create({
            'name': 'Test Customer',
            'company_id': self.env.company.id,
            'country_id': self.mozambique.id,
            'customer_rank': 1,  # É um cliente
        })
        
        # Check that receivable account was assigned to standard field
        self.assertTrue(partner.property_account_receivable_id,
                       "Campo receivable deveria estar preenchido")
        
        # Check account code format
        expected_prefix = "4111"  # 411 + 1 (national)
        self.assertTrue(partner.property_account_receivable_id.code.startswith(expected_prefix),
                       f"Código deveria começar com {expected_prefix}")
        
        # Check no dynamic accounts of receivable type
        receivable_dynamic = partner.dynamic_account_ids.filtered(
            lambda a: a.account_type == 'asset_receivable'
        )
        self.assertEqual(len(receivable_dynamic), 0,
                        "Não deveria haver contas receivable dinâmicas quando há apenas uma configuração")
    
    def test_02_payable_account_to_standard_field(self):
        """Testa se conta liability_payable vai para property_account_payable_id"""
        
        # Create payable configuration
        payable_config = self.ChartAccount.create({
            'prefix': '221',
            'name': 'Fornecedores Nacionais',
            'account_type': 'liability_payable',
            'reconcile': True,
            'partner_limite': 4,
            'company_ids': [(4, self.env.company.id)]
        })
        
        # Create partner
        partner = self.Partner.create({
            'name': 'Test Supplier',
            'company_id': self.env.company.id,
            'country_id': self.mozambique.id,
            'supplier_rank': 1,  # É um fornecedor
        })
        
        # Check that payable account was assigned to standard field
        self.assertTrue(partner.property_account_payable_id,
                       "Campo payable deveria estar preenchido")
        
        # Check account code format
        expected_prefix = "2211"  # 221 + 1 (national)
        self.assertTrue(partner.property_account_payable_id.code.startswith(expected_prefix),
                       f"Código deveria começar com {expected_prefix}")
        
        # Check no dynamic accounts of payable type
        payable_dynamic = partner.dynamic_account_ids.filtered(
            lambda a: a.account_type == 'liability_payable'
        )
        self.assertEqual(len(payable_dynamic), 0,
                        "Não deveria haver contas payable dinâmicas quando há apenas uma configuração")
    
    def test_03_other_accounts_remain_dynamic(self):
        """Testa se contas de outros tipos permanecem como dinâmicas"""
        
        # Create configuration for other account type
        other_config = self.ChartAccount.create({
            'prefix': '123',
            'name': 'Conta Especial',
            'account_type': 'asset_current',  # Tipo diferente
            'reconcile': False,
            'partner_limite': 4,
            'company_ids': [(4, self.env.company.id)]
        })
        
        # Create partner
        partner = self.Partner.create({
            'name': 'Test Partner with Special Account',
            'company_id': self.env.company.id,
            'country_id': self.mozambique.id,
        })
        
        # Check that other account type is in dynamic accounts
        self.assertTrue(len(partner.dynamic_account_ids) > 0,
                       "Deveria haver contas dinâmicas")
        
        # Check account is of correct type
        special_account = partner.dynamic_account_ids.filtered(
            lambda a: a.account_type == 'asset_current'
        )
        self.assertEqual(len(special_account), 1,
                        "Deveria haver exatamente uma conta asset_current dinâmica")
        
        # Standard fields should not be affected by other account types
        # (unless there are also receivable/payable configs)
        if not partner.property_account_receivable_id:
            print("No receivable account assigned (expected when no receivable config)")
        if not partner.property_account_payable_id:
            print("No payable account assigned (expected when no payable config)")
    
    def test_04_multiple_configs_same_type(self):
        """Testa comportamento com múltiplas configurações do mesmo tipo"""
        
        # Create multiple receivable configurations
        receivable_config1 = self.ChartAccount.create({
            'prefix': '411',
            'name': 'Clientes Tipo 1',
            'account_type': 'asset_receivable',
            'reconcile': True,
            'partner_limite': 4,
            'company_ids': [(4, self.env.company.id)]
        })
        
        receivable_config2 = self.ChartAccount.create({
            'prefix': '412',
            'name': 'Clientes Tipo 2',
            'account_type': 'asset_receivable',
            'reconcile': True,
            'partner_limite': 4,
            'company_ids': [(4, self.env.company.id)]
        })
        
        # Create partner
        partner = self.Partner.create({
            'name': 'Test Customer Multiple Configs',
            'company_id': self.env.company.id,
            'country_id': self.mozambique.id,
            'customer_rank': 1,
        })
        
        # First config should go to standard field
        self.assertTrue(partner.property_account_receivable_id,
                       "Campo receivable deveria estar preenchido")
        self.assertTrue(partner.property_account_receivable_id.code.startswith("411"),
                       "Primeira configuração deveria ser usada para campo padrão")
        
        # Second config should create dynamic account
        receivable_dynamic = partner.dynamic_account_ids.filtered(
            lambda a: a.account_type == 'asset_receivable'
        )
        self.assertEqual(len(receivable_dynamic), 1,
                        "Segunda configuração deveria criar conta dinâmica")
        self.assertTrue(receivable_dynamic[0].code.startswith("412"),
                       "Conta dinâmica deveria usar segundo prefixo")
    
    def test_05_mixed_account_types(self):
        """Testa parceiro com múltiplos tipos de conta"""
        
        # Create configurations for different account types
        receivable_config = self.ChartAccount.create({
            'prefix': '411',
            'name': 'Clientes',
            'account_type': 'asset_receivable',
            'reconcile': True,
            'partner_limite': 4,
            'company_ids': [(4, self.env.company.id)]
        })
        
        payable_config = self.ChartAccount.create({
            'prefix': '221',
            'name': 'Fornecedores',
            'account_type': 'liability_payable',
            'reconcile': True,
            'partner_limite': 4,
            'company_ids': [(4, self.env.company.id)]
        })
        
        special_config = self.ChartAccount.create({
            'prefix': '456',
            'name': 'Conta Transitória',
            'account_type': 'asset_prepayments',
            'reconcile': True,
            'partner_limite': 4,
            'company_ids': [(4, self.env.company.id)]
        })
        
        # Create partner that is both customer and supplier
        partner = self.Partner.create({
            'name': 'Test Partner Mixed',
            'company_id': self.env.company.id,
            'country_id': self.mozambique.id,
            'customer_rank': 1,
            'supplier_rank': 1,
        })
        
        # Check standard fields are filled
        self.assertTrue(partner.property_account_receivable_id,
                       "Campo receivable deveria estar preenchido")
        self.assertTrue(partner.property_account_payable_id,
                       "Campo payable deveria estar preenchido")
        
        # Check codes
        self.assertTrue(partner.property_account_receivable_id.code.startswith("411"),
                       "Conta receivable deveria usar prefixo 411")
        self.assertTrue(partner.property_account_payable_id.code.startswith("221"),
                       "Conta payable deveria usar prefixo 221")
        
        # Check special account is dynamic
        special_dynamic = partner.dynamic_account_ids.filtered(
            lambda a: a.account_type == 'asset_prepayments'
        )
        self.assertEqual(len(special_dynamic), 1,
                        "Conta especial deveria estar em contas dinâmicas")
        self.assertTrue(special_dynamic[0].code.startswith("456"),
                       "Conta especial deveria usar prefixo 456")
        
        # Total dynamic accounts should be only the special ones
        print(f"Total contas dinâmicas: {len(partner.dynamic_account_ids)}")
        print(f"Tipos: {partner.dynamic_account_ids.mapped('account_type')}")