from odoo.tests import common


class TestForceCustomAccounts(common.TransactionCase):
    """Testes para verificar se contas personalizadas substituem contas padrão do Odoo"""
    
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
        
        # Get Odoo default accounts (if they exist)
        self.odoo_default_receivable = self.Account.search([
            ('code', '=', '4110000'),
            ('account_type', '=', 'asset_receivable')
        ], limit=1)
        
        self.odoo_default_payable = self.Account.search([
            ('code', '=', '4210000'),
            ('account_type', '=', 'liability_payable')
        ], limit=1)
    
    def test_01_force_replace_receivable_account(self):
        """Testa se conta receivable personalizada substitui conta padrão do Odoo"""
        
        # Create receivable configuration
        receivable_config = self.ChartAccount.create({
            'prefix': '411',
            'name': 'Clientes Personalizados',
            'account_type': 'asset_receivable',
            'reconcile': True,
            'partner_limite': 4,
            'company_ids': [(4, self.env.company.id)]
        })
        
        # Create partner (Odoo will assign default accounts)
        partner = self.Partner.create({
            'name': 'Test Customer Force',
            'company_id': self.env.company.id,
            'country_id': self.mozambique.id,
            'customer_rank': 1,
        })
        
        # Check that custom account replaced default
        self.assertTrue(partner.property_account_receivable_id,
                       "Campo receivable deve estar preenchido")
        
        # Check it's NOT the Odoo default
        if self.odoo_default_receivable:
            self.assertNotEqual(partner.property_account_receivable_id.id, 
                              self.odoo_default_receivable.id,
                              "Não deve ser a conta padrão do Odoo 4110000")
        
        # Check it IS our custom account
        expected_prefix = "4111"  # 411 + 1 (national)
        self.assertTrue(partner.property_account_receivable_id.code.startswith(expected_prefix),
                       f"Deve ser nossa conta personalizada começando com {expected_prefix}")
        
        # Verify exact code with order number
        expected_code = f"4111000{partner.accg_nr_order}"
        self.assertEqual(partner.property_account_receivable_id.code, expected_code,
                        f"Código deve ser exatamente {expected_code}")
    
    def test_02_force_replace_payable_account(self):
        """Testa se conta payable personalizada substitui conta padrão do Odoo"""
        
        # Create payable configuration
        payable_config = self.ChartAccount.create({
            'prefix': '421',  # Note: using 421 like in screenshot
            'name': 'Fornecedores Personalizados',
            'account_type': 'liability_payable',
            'reconcile': True,
            'partner_limite': 4,
            'company_ids': [(4, self.env.company.id)]
        })
        
        # Create partner (Odoo will assign default accounts)
        partner = self.Partner.create({
            'name': 'Test Supplier Force',
            'company_id': self.env.company.id,
            'country_id': self.mozambique.id,
            'supplier_rank': 1,
        })
        
        # Check that custom account replaced default
        self.assertTrue(partner.property_account_payable_id,
                       "Campo payable deve estar preenchido")
        
        # Check it's NOT the Odoo default
        if self.odoo_default_payable:
            self.assertNotEqual(partner.property_account_payable_id.id,
                              self.odoo_default_payable.id,
                              "Não deve ser a conta padrão do Odoo 4210000")
        
        # Check it IS our custom account
        expected_prefix = "4211"  # 421 + 1 (national)
        self.assertTrue(partner.property_account_payable_id.code.startswith(expected_prefix),
                       f"Deve ser nossa conta personalizada começando com {expected_prefix}")
        
        # Verify exact code with order number
        expected_code = f"4211000{partner.accg_nr_order}"
        self.assertEqual(partner.property_account_payable_id.code, expected_code,
                        f"Código deve ser exatamente {expected_code}")
    
    def test_03_both_accounts_replaced_simultaneously(self):
        """Testa substituição simultânea de ambas as contas"""
        
        # Create both configurations
        receivable_config = self.ChartAccount.create({
            'prefix': '411',
            'name': 'Clientes',
            'account_type': 'asset_receivable',
            'reconcile': True,
            'partner_limite': 4,
            'company_ids': [(4, self.env.company.id)]
        })
        
        payable_config = self.ChartAccount.create({
            'prefix': '421',
            'name': 'Fornecedores',
            'account_type': 'liability_payable',
            'reconcile': True,
            'partner_limite': 4,
            'company_ids': [(4, self.env.company.id)]
        })
        
        # Create partner with specific order number
        partner = self.Partner.create({
            'name': 'Test Partner Both',
            'company_id': self.env.company.id,
            'country_id': self.mozambique.id,
            'customer_rank': 1,
            'supplier_rank': 1,
        })
        
        # Both should be replaced with custom accounts
        self.assertTrue(partner.property_account_receivable_id,
                       "Campo receivable deve estar preenchido")
        self.assertTrue(partner.property_account_payable_id,
                       "Campo payable deve estar preenchido")
        
        # Check codes match expected pattern
        order_str = str(partner.accg_nr_order).zfill(4)
        expected_receivable = f"4111{order_str}"
        expected_payable = f"4211{order_str}"
        
        self.assertEqual(partner.property_account_receivable_id.code, expected_receivable,
                        f"Receivable deve ser {expected_receivable}")
        self.assertEqual(partner.property_account_payable_id.code, expected_payable,
                        f"Payable deve ser {expected_payable}")
        
        print(f"✓ Partner #{partner.accg_nr_order}")
        print(f"✓ Receivable: {partner.property_account_receivable_id.code}")
        print(f"✓ Payable: {partner.property_account_payable_id.code}")
    
    def test_04_verify_no_duplicate_in_dynamic_accounts(self):
        """Verifica que contas atribuídas aos campos padrão não aparecem em contas dinâmicas"""
        
        # Create configurations
        receivable_config = self.ChartAccount.create({
            'prefix': '411',
            'name': 'Clientes',
            'account_type': 'asset_receivable',
            'reconcile': True,
            'partner_limite': 4,
            'company_ids': [(4, self.env.company.id)]
        })
        
        payable_config = self.ChartAccount.create({
            'prefix': '421',
            'name': 'Fornecedores',
            'account_type': 'liability_payable',
            'reconcile': True,
            'partner_limite': 4,
            'company_ids': [(4, self.env.company.id)]
        })
        
        other_config = self.ChartAccount.create({
            'prefix': '419',
            'name': 'Adiantamentos',
            'account_type': 'asset_current',
            'reconcile': False,
            'partner_limite': 4,
            'company_ids': [(4, self.env.company.id)]
        })
        
        # Create partner
        partner = self.Partner.create({
            'name': 'Test No Duplicates',
            'company_id': self.env.company.id,
            'country_id': self.mozambique.id,
        })
        
        # Get accounts assigned to standard fields
        receivable_id = partner.property_account_receivable_id.id if partner.property_account_receivable_id else None
        payable_id = partner.property_account_payable_id.id if partner.property_account_payable_id else None
        
        # Check dynamic accounts don't include standard ones
        dynamic_ids = partner.dynamic_account_ids.ids
        
        if receivable_id:
            self.assertNotIn(receivable_id, dynamic_ids,
                           "Conta receivable não deve aparecer em contas dinâmicas")
        
        if payable_id:
            self.assertNotIn(payable_id, dynamic_ids,
                           "Conta payable não deve aparecer em contas dinâmicas")
        
        # Only other types should be in dynamic accounts
        for account in partner.dynamic_account_ids:
            self.assertNotIn(account.account_type, ['asset_receivable', 'liability_payable'],
                           f"Conta {account.code} do tipo {account.account_type} não deveria estar em dinâmicas")
        
        print(f"✓ Receivable em campo padrão: {partner.property_account_receivable_id.code if partner.property_account_receivable_id else 'None'}")
        print(f"✓ Payable em campo padrão: {partner.property_account_payable_id.code if partner.property_account_payable_id else 'None'}")
        print(f"✓ Contas dinâmicas: {[a.code for a in partner.dynamic_account_ids]}")