from odoo.tests import common


class TestCustomerSupplierDistinction(common.TransactionCase):
    """Testes para verificar distinção cliente/fornecedor e ausência de duplicação"""
    
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
        
        # Create standard configurations
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
    
    def test_01_customer_only(self):
        """Teste para parceiro que é APENAS cliente"""
        
        # Create customer (customer_rank > 0, supplier_rank = 0)
        partner = self.Partner.create({
            'name': 'Cliente Teste',
            'company_id': self.env.company.id,
            'country_id': self.mozambique.id,
            'customer_rank': 1,
            'supplier_rank': 0,
        })
        
        # Verificar que APENAS receivable foi preenchido
        self.assertTrue(partner.property_account_receivable_id,
                       "Cliente deve ter conta receivable")
        self.assertFalse(partner.property_account_payable_id,
                        "Cliente NÃO deve ter conta payable")
        
        # Verificar código correto
        expected_receivable = f"4111{str(partner.accg_nr_order).zfill(4)}"
        self.assertEqual(partner.property_account_receivable_id.code, expected_receivable,
                        f"Código receivable deve ser {expected_receivable}")
        
        # Verificar que não há duplicação nas dinâmicas
        receivable_in_dynamic = partner.dynamic_account_ids.filtered(
            lambda a: a.id == partner.property_account_receivable_id.id
        )
        self.assertEqual(len(receivable_in_dynamic), 0,
                        "Conta receivable NÃO deve aparecer nas dinâmicas")
        
        # Verificar conta especial nas dinâmicas
        special_accounts = partner.dynamic_account_ids.filtered(
            lambda a: a.code.startswith('419')
        )
        self.assertEqual(len(special_accounts), 1,
                        "Deve ter conta especial (419) nas dinâmicas")
        
        print(f"✓ Cliente #{partner.accg_nr_order}")
        print(f"  Receivable: {partner.property_account_receivable_id.code}")
        print(f"  Payable: {'Vazio' if not partner.property_account_payable_id else partner.property_account_payable_id.code}")
        print(f"  Dinâmicas: {[a.code for a in partner.dynamic_account_ids]}")
    
    def test_02_supplier_only(self):
        """Teste para parceiro que é APENAS fornecedor"""
        
        # Create supplier (customer_rank = 0, supplier_rank > 0)
        partner = self.Partner.create({
            'name': 'Fornecedor Teste',
            'company_id': self.env.company.id,
            'country_id': self.mozambique.id,
            'customer_rank': 0,
            'supplier_rank': 1,
        })
        
        # Verificar que APENAS payable foi preenchido
        self.assertFalse(partner.property_account_receivable_id,
                        "Fornecedor NÃO deve ter conta receivable")
        self.assertTrue(partner.property_account_payable_id,
                       "Fornecedor deve ter conta payable")
        
        # Verificar código correto
        expected_payable = f"4211{str(partner.accg_nr_order).zfill(4)}"
        self.assertEqual(partner.property_account_payable_id.code, expected_payable,
                        f"Código payable deve ser {expected_payable}")
        
        # Verificar que não há duplicação nas dinâmicas
        payable_in_dynamic = partner.dynamic_account_ids.filtered(
            lambda a: a.id == partner.property_account_payable_id.id
        )
        self.assertEqual(len(payable_in_dynamic), 0,
                        "Conta payable NÃO deve aparecer nas dinâmicas")
        
        # Verificar conta especial nas dinâmicas
        special_accounts = partner.dynamic_account_ids.filtered(
            lambda a: a.code.startswith('419')
        )
        self.assertEqual(len(special_accounts), 1,
                        "Deve ter conta especial (419) nas dinâmicas")
        
        print(f"✓ Fornecedor #{partner.accg_nr_order}")
        print(f"  Receivable: {'Vazio' if not partner.property_account_receivable_id else partner.property_account_receivable_id.code}")
        print(f"  Payable: {partner.property_account_payable_id.code}")
        print(f"  Dinâmicas: {[a.code for a in partner.dynamic_account_ids]}")
    
    def test_03_customer_and_supplier(self):
        """Teste para parceiro que é cliente E fornecedor"""
        
        # Create partner that is both (customer_rank > 0, supplier_rank > 0)
        partner = self.Partner.create({
            'name': 'Cliente e Fornecedor Teste',
            'company_id': self.env.company.id,
            'country_id': self.mozambique.id,
            'customer_rank': 1,
            'supplier_rank': 1,
        })
        
        # Verificar que AMBAS foram preenchidas
        self.assertTrue(partner.property_account_receivable_id,
                       "Cliente+Fornecedor deve ter conta receivable")
        self.assertTrue(partner.property_account_payable_id,
                       "Cliente+Fornecedor deve ter conta payable")
        
        # Verificar códigos corretos
        expected_receivable = f"4111{str(partner.accg_nr_order).zfill(4)}"
        expected_payable = f"4211{str(partner.accg_nr_order).zfill(4)}"
        
        self.assertEqual(partner.property_account_receivable_id.code, expected_receivable,
                        f"Código receivable deve ser {expected_receivable}")
        self.assertEqual(partner.property_account_payable_id.code, expected_payable,
                        f"Código payable deve ser {expected_payable}")
        
        # Verificar que NÃO há duplicação nas dinâmicas
        standard_ids = [
            partner.property_account_receivable_id.id,
            partner.property_account_payable_id.id
        ]
        duplicates_in_dynamic = partner.dynamic_account_ids.filtered(
            lambda a: a.id in standard_ids
        )
        self.assertEqual(len(duplicates_in_dynamic), 0,
                        "Contas padrão NÃO devem aparecer nas dinâmicas")
        
        # Verificar conta especial nas dinâmicas
        special_accounts = partner.dynamic_account_ids.filtered(
            lambda a: a.code.startswith('419')
        )
        self.assertEqual(len(special_accounts), 1,
                        "Deve ter conta especial (419) nas dinâmicas")
        
        print(f"✓ Cliente+Fornecedor #{partner.accg_nr_order}")
        print(f"  Receivable: {partner.property_account_receivable_id.code}")
        print(f"  Payable: {partner.property_account_payable_id.code}")
        print(f"  Dinâmicas: {[a.code for a in partner.dynamic_account_ids]}")
    
    def test_04_neither_customer_nor_supplier(self):
        """Teste para parceiro que NÃO é cliente NEM fornecedor (contato neutro)"""
        
        # Create neutral contact (customer_rank = 0, supplier_rank = 0)
        partner = self.Partner.create({
            'name': 'Contato Neutro Teste',
            'company_id': self.env.company.id,
            'country_id': self.mozambique.id,
            'customer_rank': 0,
            'supplier_rank': 0,
        })
        
        # Verificar que NENHUMA conta padrão foi preenchida com nossas contas
        # (Odoo pode atribuir contas padrão próprias, mas não as nossas personalizadas)
        if partner.property_account_receivable_id:
            self.assertFalse(partner.property_account_receivable_id.code.startswith('411'),
                           "Contato neutro NÃO deve ter nossa conta receivable personalizada")
        
        if partner.property_account_payable_id:
            self.assertFalse(partner.property_account_payable_id.code.startswith('421'),
                           "Contato neutro NÃO deve ter nossa conta payable personalizada")
        
        # Verificar que contas receivable/payable foram para dinâmicas
        receivable_in_dynamic = partner.dynamic_account_ids.filtered(
            lambda a: a.code.startswith('411')
        )
        payable_in_dynamic = partner.dynamic_account_ids.filtered(
            lambda a: a.code.startswith('421')
        )
        
        self.assertEqual(len(receivable_in_dynamic), 1,
                        "Conta receivable deve estar nas dinâmicas para contato neutro")
        self.assertEqual(len(payable_in_dynamic), 1,
                        "Conta payable deve estar nas dinâmicas para contato neutro")
        
        # Verificar conta especial nas dinâmicas
        special_accounts = partner.dynamic_account_ids.filtered(
            lambda a: a.code.startswith('419')
        )
        self.assertEqual(len(special_accounts), 1,
                        "Deve ter conta especial (419) nas dinâmicas")
        
        print(f"✓ Contato Neutro #{partner.accg_nr_order}")
        print(f"  Receivable: {'Padrão Odoo' if partner.property_account_receivable_id else 'Vazio'}")
        print(f"  Payable: {'Padrão Odoo' if partner.property_account_payable_id else 'Vazio'}")
        print(f"  Dinâmicas: {[a.code for a in partner.dynamic_account_ids]}")
    
    def test_05_no_duplication_in_dynamic_accounts(self):
        """Teste específico para garantir ausência de duplicação"""
        
        # Create customer+supplier
        partner = self.Partner.create({
            'name': 'Teste Sem Duplicação',
            'company_id': self.env.company.id,
            'country_id': self.mozambique.id,
            'customer_rank': 1,
            'supplier_rank': 1,
        })
        
        # Coletar todos os códigos de contas
        all_codes = []
        
        if partner.property_account_receivable_id:
            all_codes.append(partner.property_account_receivable_id.code)
        
        if partner.property_account_payable_id:
            all_codes.append(partner.property_account_payable_id.code)
        
        dynamic_codes = partner.dynamic_account_ids.mapped('code')
        
        # Verificar que não há sobreposição
        overlap = set(all_codes) & set(dynamic_codes)
        self.assertEqual(len(overlap), 0,
                        f"Não deve haver contas duplicadas. Sobreposição encontrada: {overlap}")
        
        # Verificar que cada tipo está no lugar correto
        self.assertTrue(partner.property_account_receivable_id.code.startswith('411'),
                       "Receivable deve estar no campo padrão")
        self.assertTrue(partner.property_account_payable_id.code.startswith('421'),
                       "Payable deve estar no campo padrão")
        
        # Apenas conta especial deve estar nas dinâmicas
        for account in partner.dynamic_account_ids:
            self.assertNotIn(account.code[:3], ['411', '421'],
                           f"Conta {account.code} não deveria estar nas dinâmicas")
        
        print(f"✓ Sem Duplicação #{partner.accg_nr_order}")
        print(f"  Campos padrão: {all_codes}")
        print(f"  Dinâmicas: {dynamic_codes}")
        print(f"  Sobreposição: {overlap if overlap else 'Nenhuma ✓'}")