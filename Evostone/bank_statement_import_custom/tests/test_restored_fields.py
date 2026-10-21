from odoo.tests import common
from odoo.exceptions import ValidationError


class TestRestoredFields(common.TransactionCase):
    """Testes para verificar campos padrão restaurados e contas dinâmicas"""
    
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
        
        # Get default accounts
        self.default_receivable = self.env.company.account_default_pos_receivable_account_id
        self.default_payable = self.env['account.account'].search([
            ('account_type', '=', 'liability_payable')
        ], limit=1)
        
        # Create test chart configuration for dynamic accounts
        self.chart_config = self.ChartAccount.create({
            'prefix': '411',
            'name': 'Clientes Teste',
            'account_type': 'asset_receivable',
            'reconcile': True,
            'partner_limite': 4,
            'company_ids': [(4, self.env.company.id)]
        })
    
    def test_01_default_fields_not_forced_to_false(self):
        """Testa se campos padrão não são mais forçados para False"""
        # Create partner
        partner = self.Partner.create({
            'name': 'Test Partner 01',
            'company_id': self.env.company.id,
            'country_id': self.mozambique.id,
        })
        
        # Check that default account fields can be set (not forced to False)
        # Note: They might still be False initially, but should be settable
        print(f"Initial payable: {partner.property_account_payable_id}")
        print(f"Initial receivable: {partner.property_account_receivable_id}")
        
        # Try to set accounts
        if self.default_payable:
            partner.property_account_payable_id = self.default_payable
            self.assertEqual(partner.property_account_payable_id, self.default_payable,
                           "Campo payable deveria aceitar valor atribuído")
        
        if self.default_receivable:
            partner.property_account_receivable_id = self.default_receivable
            self.assertEqual(partner.property_account_receivable_id, self.default_receivable,
                           "Campo receivable deveria aceitar valor atribuído")
    
    def test_02_dynamic_accounts_still_created(self):
        """Testa se contas dinâmicas continuam sendo criadas"""
        # Create partner
        partner = self.Partner.create({
            'name': 'Test Partner 02',
            'company_id': self.env.company.id,
            'country_id': self.mozambique.id,
        })
        
        # Check accg_nr_order was assigned
        self.assertTrue(partner.accg_nr_order > 0,
                       "accg_nr_order deveria ser atribuído")
        
        # Check dynamic accounts were created
        self.assertTrue(len(partner.dynamic_account_ids) > 0,
                       "Contas dinâmicas deveriam ser criadas")
        
        # Check account code format
        for account in partner.dynamic_account_ids:
            expected_prefix = self.chart_config.prefix + "1"  # National
            self.assertTrue(account.code.startswith(expected_prefix),
                          f"Código da conta {account.code} deveria começar com {expected_prefix}")
    
    def test_03_both_systems_work_together(self):
        """Testa se ambos sistemas funcionam em conjunto"""
        # Create partner
        partner = self.Partner.create({
            'name': 'Test Partner 03',
            'company_id': self.env.company.id,
            'country_id': self.mozambique.id,
        })
        
        # Partner should have dynamic accounts
        self.assertTrue(len(partner.dynamic_account_ids) > 0,
                       "Contas dinâmicas deveriam existir")
        
        # Partner can also have default accounts
        if self.default_payable:
            partner.property_account_payable_id = self.default_payable
            self.assertTrue(partner.property_account_payable_id,
                          "Campo payable deveria aceitar valor")
        
        # Both systems coexist
        print(f"Partner has {len(partner.dynamic_account_ids)} dynamic accounts")
        print(f"Partner payable account: {partner.property_account_payable_id.code if partner.property_account_payable_id else 'None'}")
        print(f"Partner receivable account: {partner.property_account_receivable_id.code if partner.property_account_receivable_id else 'None'}")
        
        # No conflict between systems
        self.assertEqual(partner.name, 'Test Partner 03',
                        "Partner deveria ser criado sem conflitos")
    
    def test_04_no_validation_errors(self):
        """Testa se não há erros de validação ao criar parceiros"""
        try:
            # Create partner without setting default accounts
            partner = self.Partner.create({
                'name': 'Test Partner 04',
                'company_id': self.env.company.id,
                'country_id': self.mozambique.id,
            })
            
            # Should create successfully
            self.assertTrue(partner.id, "Partner deveria ser criado sem erros")
            
            # Update partner
            partner.write({'name': 'Test Partner 04 Updated'})
            self.assertEqual(partner.name, 'Test Partner 04 Updated',
                           "Partner deveria ser atualizado sem erros")
            
        except ValidationError as e:
            self.fail(f"Não deveria haver erro de validação: {e}")