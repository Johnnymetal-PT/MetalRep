from odoo.tests import common
from odoo.exceptions import ValidationError


class TestDynamicAccounts(common.TransactionCase):
    
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
        self.south_africa = self.Country.search([('code', '=', 'ZA')], limit=1)
        
        # Ensure we have test countries
        if not self.mozambique:
            self.mozambique = self.Country.create({
                'name': 'Mozambique',
                'code': 'MZ'
            })
        if not self.south_africa:
            self.south_africa = self.Country.create({
                'name': 'South Africa', 
                'code': 'ZA'
            })
        
        # Set company country
        self.env.company.country_id = self.mozambique
        
        # Create test chart configurations
        self.chart_config_1 = self.ChartAccount.create({
            'prefix': '411',
            'name': 'Clientes Nacionais',
            'account_type': 'asset_receivable',
            'reconcile': True,
            'partner_limite': 4,
            'company_ids': [(4, self.env.company.id)]
        })
        
        self.chart_config_2 = self.ChartAccount.create({
            'prefix': '221',
            'name': 'Fornecedores',
            'account_type': 'liability_payable',
            'reconcile': True,
            'partner_limite': 3,
            'non_trade': False,
            'deprecated': False,
            'company_ids': [(4, self.env.company.id)]
        })
    
    def test_01_create_partner_same_country(self):
        """Test creating partner with same country as company"""
        
        # Create partner with same country as company
        partner = self.Partner.create({
            'name': 'Test Client Mozambique',
            'country_id': self.mozambique.id,
            'company_id': self.env.company.id,
        })
        
        # Check accg_nr_order was assigned
        self.assertTrue(partner.accg_nr_order > 0, "Partner should have accg_nr_order assigned")
        
        # Check dynamic accounts were created
        dynamic_accounts = partner.dynamic_account_ids
        self.assertEqual(len(dynamic_accounts), 2, "Should have 2 dynamic accounts created")
        
        # Check account codes follow formula: PREFIX + 1 (same country) + padded order
        expected_codes = [
            '41110001',  # 411 + 1 + 0001
            '2211001'    # 221 + 1 + 001
        ]
        
        account_codes = dynamic_accounts.mapped('code')
        for expected_code in expected_codes:
            self.assertIn(expected_code, account_codes, f"Account code {expected_code} should be created")
    
    def test_02_create_partner_different_country(self):
        """Test creating partner with different country from company"""
        
        # Create partner with different country
        partner = self.Partner.create({
            'name': 'Test Client South Africa',
            'country_id': self.south_africa.id,
            'company_id': self.env.company.id,
        })
        
        # Check dynamic accounts were created with country code 2
        dynamic_accounts = partner.dynamic_account_ids
        
        # Assuming this is the second partner (accg_nr_order = 2)
        expected_codes = [
            '41120002',  # 411 + 2 (different country) + 0002
            '2212002'    # 221 + 2 + 002
        ]
        
        account_codes = dynamic_accounts.mapped('code')
        for expected_code in expected_codes:
            self.assertIn(expected_code, account_codes, f"Account code {expected_code} should be created")
    
    def test_03_partner_required_fields(self):
        """Test that company_id and country_id are required"""
        
        # Test creating partner without company_id should fail
        with self.assertRaises(ValidationError):
            partner = self.Partner.create({
                'name': 'Test Partner No Company',
                'country_id': self.mozambique.id,
            })
            partner.company_id = False
            
        # Test creating partner without country_id should auto-assign
        partner = self.Partner.create({
            'name': 'Test Partner Auto Country',
            'company_id': self.env.company.id,
        })
        
        # Should have country assigned (either from company or default)
        self.assertTrue(partner.country_id, "Partner should have country_id assigned automatically")
    
    def test_04_account_fields_disabled(self):
        """Test that default account fields are disabled"""
        
        partner = self.Partner.create({
            'name': 'Test Disabled Account Fields',
            'country_id': self.mozambique.id,
            'company_id': self.env.company.id,
        })
        
        # Check that account fields are False/disabled
        self.assertFalse(partner.property_account_payable_id, "Payable account should be disabled")
        self.assertFalse(partner.property_account_receivable_id, "Receivable account should be disabled")
        
        # Try to set account fields - should be forced to False
        partner.write({
            'property_account_payable_id': 1,
            'property_account_receivable_id': 1,
        })
        
        self.assertFalse(partner.property_account_payable_id, "Payable account should remain disabled")
        self.assertFalse(partner.property_account_receivable_id, "Receivable account should remain disabled")
    
    def test_05_sequential_accg_nr_order(self):
        """Test that accg_nr_order increments sequentially"""
        
        # Get initial max order
        partners_before = self.Partner.search([], order='accg_nr_order desc', limit=1)
        initial_max = partners_before.accg_nr_order if partners_before else 0
        
        # Create multiple partners
        partner1 = self.Partner.create({
            'name': 'Sequential Test 1',
            'country_id': self.mozambique.id,
            'company_id': self.env.company.id,
        })
        
        partner2 = self.Partner.create({
            'name': 'Sequential Test 2',
            'country_id': self.mozambique.id,
            'company_id': self.env.company.id,
        })
        
        partner3 = self.Partner.create({
            'name': 'Sequential Test 3',
            'country_id': self.mozambique.id,
            'company_id': self.env.company.id,
        })
        
        # Check sequential ordering
        self.assertEqual(partner1.accg_nr_order, initial_max + 1)
        self.assertEqual(partner2.accg_nr_order, initial_max + 2)
        self.assertEqual(partner3.accg_nr_order, initial_max + 3)
    
    def test_06_account_field_mapping(self):
        """Test that all fields from chart config are mapped to account"""
        
        # Create chart config with all fields
        tag = self.env['account.account.tag'].create({'name': 'Test Tag'})
        journal = self.env['account.journal'].search([], limit=1)
        
        chart_config = self.ChartAccount.create({
            'prefix': '512',
            'name': 'Test Full Config',
            'account_type': 'expense',
            'reconcile': True,
            'partner_limite': 5,
            'non_trade': True,
            'deprecated': True,
            'tag_ids': [(4, tag.id)],
            'allowed_journal_ids': [(4, journal.id)] if journal else False,
            'company_ids': [(4, self.env.company.id)]
        })
        
        # Create partner
        partner = self.Partner.create({
            'name': 'Test Field Mapping',
            'country_id': self.mozambique.id,
            'company_id': self.env.company.id,
        })
        
        # Find the created account for this config
        account = partner.dynamic_account_ids.filtered(
            lambda a: a.code.startswith('512')
        )
        
        # Verify field mapping
        self.assertTrue(account, "Account should be created")
        self.assertEqual(account.account_type, 'expense', "Account type should match")
        self.assertTrue(account.reconcile, "Reconcile should match")
        self.assertTrue(account.non_trade, "Non-trade should match")
        self.assertTrue(account.deprecated, "Deprecated should match")
        self.assertIn(tag, account.tag_ids, "Tags should be mapped")
        if journal:
            self.assertIn(journal, account.allowed_journal_ids, "Journals should be mapped")