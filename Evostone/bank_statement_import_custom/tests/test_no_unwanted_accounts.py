from odoo.tests import common


class TestNoUnwantedAccounts(common.TransactionCase):
    """Testes para garantir que não são criadas contas indevidas"""
    
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
        
        # Create all types of configurations
        self.receivable_config = self.ChartAccount.create({
            'prefix': '411',
            'name': 'Conta corrente de cliente',
            'account_type': 'asset_receivable',
            'reconcile': True,
            'partner_limite': 4,
            'company_ids': [(4, self.env.company.id)]
        })
        
        self.payable_config = self.ChartAccount.create({
            'prefix': '421',
            'name': 'Conta corrente de fornecedor',
            'account_type': 'liability_payable',
            'reconcile': True,
            'partner_limite': 4,
            'company_ids': [(4, self.env.company.id)]
        })
        
        self.special_config = self.ChartAccount.create({
            'prefix': '419',
            'name': 'Conta adiantamento',
            'account_type': 'asset_current',
            'reconcile': False,
            'partner_limite': 4,
            'company_ids': [(4, self.env.company.id)]
        })
    
    def test_01_customer_no_payable_accounts(self):
        """Cliente NÃO deve ter contas de fornecedor (421) criadas"""
        
        # Create customer only
        partner = self.Partner.create({
            'name': 'Cliente Sem Conta Fornecedor',
            'company_id': self.env.company.id,
            'country_id': self.mozambique.id,
            'customer_rank': 1,
            'supplier_rank': 0,
        })
        
        # Verificar campo padrão
        self.assertTrue(partner.property_account_receivable_id,
                       "Cliente deve ter conta receivable")
        
        # Verificar que NÃO há contas payable (421) nas dinâmicas
        payable_in_dynamic = partner.dynamic_account_ids.filtered(
            lambda a: a.code.startswith('421')
        )
        self.assertEqual(len(payable_in_dynamic), 0,
                        "Cliente NÃO deve ter contas de fornecedor (421) nas dinâmicas")
        
        # Verificar que há conta especial (419)
        special_in_dynamic = partner.dynamic_account_ids.filtered(
            lambda a: a.code.startswith('419')
        )
        self.assertEqual(len(special_in_dynamic), 1,
                        "Cliente deve ter conta especial (419)")
        
        # Verificar que NÃO há conta receivable duplicada nas dinâmicas
        receivable_in_dynamic = partner.dynamic_account_ids.filtered(
            lambda a: a.code.startswith('411')
        )
        self.assertEqual(len(receivable_in_dynamic), 0,
                        "Conta receivable não deve estar duplicada nas dinâmicas")
        
        print(f"✅ Cliente #{partner.accg_nr_order}")
        print(f"   Receivable: {partner.property_account_receivable_id.code}")
        print(f"   Dinâmicas: {[a.code for a in partner.dynamic_account_ids]}")
        print(f"   Verificação: SEM contas 421 ✓")
    
    def test_02_supplier_no_receivable_accounts(self):
        """Fornecedor NÃO deve ter contas de cliente (411) criadas"""
        
        # Create supplier only
        partner = self.Partner.create({
            'name': 'Fornecedor Sem Conta Cliente',
            'company_id': self.env.company.id,
            'country_id': self.mozambique.id,
            'customer_rank': 0,
            'supplier_rank': 1,
        })
        
        # Verificar campo padrão
        self.assertTrue(partner.property_account_payable_id,
                       "Fornecedor deve ter conta payable")
        
        # Verificar que NÃO há contas receivable (411) nas dinâmicas
        receivable_in_dynamic = partner.dynamic_account_ids.filtered(
            lambda a: a.code.startswith('411')
        )
        self.assertEqual(len(receivable_in_dynamic), 0,
                        "Fornecedor NÃO deve ter contas de cliente (411) nas dinâmicas")
        
        # Verificar que há conta especial (419)
        special_in_dynamic = partner.dynamic_account_ids.filtered(
            lambda a: a.code.startswith('419')
        )
        self.assertEqual(len(special_in_dynamic), 1,
                        "Fornecedor deve ter conta especial (419)")
        
        # Verificar que NÃO há conta payable duplicada nas dinâmicas
        payable_in_dynamic = partner.dynamic_account_ids.filtered(
            lambda a: a.code.startswith('421')
        )
        self.assertEqual(len(payable_in_dynamic), 0,
                        "Conta payable não deve estar duplicada nas dinâmicas")
        
        print(f"✅ Fornecedor #{partner.accg_nr_order}")
        print(f"   Payable: {partner.property_account_payable_id.code}")
        print(f"   Dinâmicas: {[a.code for a in partner.dynamic_account_ids]}")
        print(f"   Verificação: SEM contas 411 ✓")
    
    def test_03_customer_and_supplier_has_both(self):
        """Cliente+Fornecedor deve ter AMBAS as contas nos campos padrão"""
        
        # Create customer and supplier
        partner = self.Partner.create({
            'name': 'Cliente e Fornecedor',
            'company_id': self.env.company.id,
            'country_id': self.mozambique.id,
            'customer_rank': 1,
            'supplier_rank': 1,
        })
        
        # Verificar campos padrão
        self.assertTrue(partner.property_account_receivable_id,
                       "Cliente+Fornecedor deve ter conta receivable")
        self.assertTrue(partner.property_account_payable_id,
                       "Cliente+Fornecedor deve ter conta payable")
        
        # Verificar códigos
        self.assertTrue(partner.property_account_receivable_id.code.startswith('411'),
                       "Receivable deve ser 411...")
        self.assertTrue(partner.property_account_payable_id.code.startswith('421'),
                       "Payable deve ser 421...")
        
        # Verificar que NÃO há duplicação nas dinâmicas
        receivable_in_dynamic = partner.dynamic_account_ids.filtered(
            lambda a: a.code.startswith('411')
        )
        payable_in_dynamic = partner.dynamic_account_ids.filtered(
            lambda a: a.code.startswith('421')
        )
        
        self.assertEqual(len(receivable_in_dynamic), 0,
                        "Receivable não deve estar nas dinâmicas")
        self.assertEqual(len(payable_in_dynamic), 0,
                        "Payable não deve estar nas dinâmicas")
        
        # Verificar conta especial
        special_in_dynamic = partner.dynamic_account_ids.filtered(
            lambda a: a.code.startswith('419')
        )
        self.assertEqual(len(special_in_dynamic), 1,
                        "Deve ter conta especial (419)")
        
        print(f"✅ Cliente+Fornecedor #{partner.accg_nr_order}")
        print(f"   Receivable: {partner.property_account_receivable_id.code}")
        print(f"   Payable: {partner.property_account_payable_id.code}")
        print(f"   Dinâmicas: {[a.code for a in partner.dynamic_account_ids]}")
        print(f"   Verificação: Apenas 419 nas dinâmicas ✓")
    
    def test_04_neutral_contact_no_accounts(self):
        """Contato neutro NÃO deve ter contas 411 ou 421 criadas"""
        
        # Create neutral contact
        partner = self.Partner.create({
            'name': 'Contato Neutro',
            'company_id': self.env.company.id,
            'country_id': self.mozambique.id,
            'customer_rank': 0,
            'supplier_rank': 0,
        })
        
        # Verificar campos padrão (podem ter contas padrão do Odoo, mas não as nossas)
        if partner.property_account_receivable_id:
            self.assertFalse(partner.property_account_receivable_id.code.startswith('411'),
                           "Contato neutro não deve ter nossa conta receivable")
        
        if partner.property_account_payable_id:
            self.assertFalse(partner.property_account_payable_id.code.startswith('421'),
                           "Contato neutro não deve ter nossa conta payable")
        
        # Verificar que NÃO há contas 411 ou 421 nas dinâmicas
        receivable_in_dynamic = partner.dynamic_account_ids.filtered(
            lambda a: a.code.startswith('411')
        )
        payable_in_dynamic = partner.dynamic_account_ids.filtered(
            lambda a: a.code.startswith('421')
        )
        
        self.assertEqual(len(receivable_in_dynamic), 0,
                        "Contato neutro NÃO deve ter contas 411 nas dinâmicas")
        self.assertEqual(len(payable_in_dynamic), 0,
                        "Contato neutro NÃO deve ter contas 421 nas dinâmicas")
        
        # Verificar conta especial
        special_in_dynamic = partner.dynamic_account_ids.filtered(
            lambda a: a.code.startswith('419')
        )
        self.assertEqual(len(special_in_dynamic), 1,
                        "Deve ter conta especial (419)")
        
        print(f"✅ Contato Neutro #{partner.accg_nr_order}")
        print(f"   Receivable: {'Padrão Odoo' if partner.property_account_receivable_id else 'Vazio'}")
        print(f"   Payable: {'Padrão Odoo' if partner.property_account_payable_id else 'Vazio'}")
        print(f"   Dinâmicas: {[a.code for a in partner.dynamic_account_ids]}")
        print(f"   Verificação: SEM contas 411 ou 421 ✓")
    
    def test_05_only_appropriate_accounts_created(self):
        """Teste resumo: apenas contas apropriadas são criadas"""
        
        # Criar vários parceiros
        customer = self.Partner.create({
            'name': 'Cliente Final',
            'company_id': self.env.company.id,
            'country_id': self.mozambique.id,
            'customer_rank': 1,
            'supplier_rank': 0,
        })
        
        supplier = self.Partner.create({
            'name': 'Fornecedor Final',
            'company_id': self.env.company.id,
            'country_id': self.mozambique.id,
            'customer_rank': 0,
            'supplier_rank': 1,
        })
        
        both = self.Partner.create({
            'name': 'Ambos Final',
            'company_id': self.env.company.id,
            'country_id': self.mozambique.id,
            'customer_rank': 1,
            'supplier_rank': 1,
        })
        
        # Verificar cliente
        self.assertFalse(any(a.code.startswith('421') for a in customer.dynamic_account_ids),
                        "Cliente não deve ter 421 nas dinâmicas")
        
        # Verificar fornecedor
        self.assertFalse(any(a.code.startswith('411') for a in supplier.dynamic_account_ids),
                        "Fornecedor não deve ter 411 nas dinâmicas")
        
        # Verificar ambos
        self.assertFalse(any(a.code.startswith('411') or a.code.startswith('421') 
                            for a in both.dynamic_account_ids),
                        "Cliente+Fornecedor não deve ter 411 ou 421 nas dinâmicas")
        
        print("\n✅ RESUMO FINAL:")
        print(f"Cliente: Dinâmicas = {[a.code for a in customer.dynamic_account_ids]}")
        print(f"Fornecedor: Dinâmicas = {[a.code for a in supplier.dynamic_account_ids]}")
        print(f"Ambos: Dinâmicas = {[a.code for a in both.dynamic_account_ids]}")
        print("Verificação: Nenhuma conta indevida criada ✓")