from odoo.tests import common
from odoo.exceptions import ValidationError


class TestNoDeletePartners(common.TransactionCase):
    """Testes para verificar que contatos não podem ser deletados"""
    
    def setUp(self):
        super().setUp()
        
        # Get models
        self.Partner = self.env['res.partner']
        self.Country = self.env['res.country']
        
        # Get or create country
        self.mozambique = self.Country.search([('code', '=', 'MZ')], limit=1)
        if not self.mozambique:
            self.mozambique = self.Country.create({
                'name': 'Mozambique',
                'code': 'MZ'
            })
        
        # Set company country
        self.env.company.country_id = self.mozambique
    
    def test_01_cannot_delete_partner(self):
        """Teste que parceiro não pode ser deletado"""
        
        # Create a partner
        partner = self.Partner.create({
            'name': 'Teste Delete Bloqueado',
            'company_id': self.env.company.id,
            'country_id': self.mozambique.id,
            'customer_rank': 1,
        })
        
        # Try to delete - should raise ValidationError
        with self.assertRaises(ValidationError) as error:
            partner.unlink()
        
        # Check error message
        self.assertIn('Não é permitido excluir contatos', str(error.exception),
                     "Mensagem de erro deve informar que exclusão não é permitida")
        
        # Verify partner still exists
        partner_exists = self.Partner.search([('id', '=', partner.id)])
        self.assertTrue(partner_exists,
                       "Parceiro deve continuar existindo após tentativa de exclusão")
        
        print(f"✅ Teste 1: Parceiro '{partner.name}' não pode ser deletado")
    
    def test_02_cannot_delete_multiple_partners(self):
        """Teste que múltiplos parceiros não podem ser deletados"""
        
        # Create multiple partners
        partners = self.Partner.create([
            {
                'name': 'Cliente Teste 1',
                'company_id': self.env.company.id,
                'country_id': self.mozambique.id,
                'customer_rank': 1,
            },
            {
                'name': 'Fornecedor Teste 1',
                'company_id': self.env.company.id,
                'country_id': self.mozambique.id,
                'supplier_rank': 1,
            },
        ])
        
        # Try to delete all - should raise ValidationError
        with self.assertRaises(ValidationError) as error:
            partners.unlink()
        
        # Check error message
        self.assertIn('Não é permitido excluir contatos', str(error.exception),
                     "Mensagem de erro deve informar que exclusão não é permitida")
        
        # Verify all partners still exist
        for partner in partners:
            partner_exists = self.Partner.search([('id', '=', partner.id)])
            self.assertTrue(partner_exists,
                           f"Parceiro '{partner.name}' deve continuar existindo")
        
        print(f"✅ Teste 2: {len(partners)} parceiros não podem ser deletados em massa")
    
    def test_03_can_deactivate_partner(self):
        """Teste que parceiro pode ser desativado (alternativa à exclusão)"""
        
        # Create a partner
        partner = self.Partner.create({
            'name': 'Teste Desativar',
            'company_id': self.env.company.id,
            'country_id': self.mozambique.id,
            'active': True,
        })
        
        # Deactivate partner (should work)
        partner.active = False
        
        # Verify partner is deactivated
        self.assertFalse(partner.active,
                        "Parceiro deve poder ser desativado")
        
        # Verify deactivated partner is not in default search
        active_partners = self.Partner.search([('name', '=', 'Teste Desativar')])
        self.assertEqual(len(active_partners), 0,
                        "Parceiro desativado não deve aparecer em busca padrão")
        
        # Verify deactivated partner still exists (with active_test=False)
        all_partners = self.Partner.with_context(active_test=False).search([
            ('name', '=', 'Teste Desativar')
        ])
        self.assertEqual(len(all_partners), 1,
                        "Parceiro desativado deve existir no banco de dados")
        
        print(f"✅ Teste 3: Parceiro pode ser desativado como alternativa à exclusão")
    
    def test_04_error_message_suggests_deactivation(self):
        """Teste que mensagem de erro sugere desativação como alternativa"""
        
        # Create a partner
        partner = self.Partner.create({
            'name': 'Teste Mensagem',
            'company_id': self.env.company.id,
            'country_id': self.mozambique.id,
        })
        
        # Try to delete
        try:
            partner.unlink()
            self.fail("Exclusão deveria ter falhado")
        except ValidationError as e:
            error_message = str(e)
            
            # Check that message suggests deactivation
            self.assertIn('desativar', error_message.lower(),
                         "Mensagem deve sugerir desativação como alternativa")
            self.assertIn('Ativo', error_message,
                         "Mensagem deve mencionar campo 'Ativo'")
            
            print(f"✅ Teste 4: Mensagem de erro sugere desativação")
            print(f"   Mensagem: {error_message}")