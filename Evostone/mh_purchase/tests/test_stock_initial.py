from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError, UserError
from datetime import datetime


@tagged('post_install', '-at_install')
class TestStockInitial(TransactionCase):
    """
    Testes para o documento de Stock Inicial com PCMP.
    """

    def setUp(self):
        super().setUp()

        # Criar categoria PCMP
        self.category_pcmp = self.env['product.category'].create({
            'name': 'Test PCMP Category',
            'property_cost_method': 'pcmp',
            'property_valuation': 'real_time',
        })

        # Criar produtos
        self.product1 = self.env['product.product'].create({
            'name': 'Product 1 PCMP',
            'type': 'product',
            'categ_id': self.category_pcmp.id,
            'standard_price': 100.0,
        })

        self.product2 = self.env['product.product'].create({
            'name': 'Product 2 PCMP',
            'type': 'product',
            'categ_id': self.category_pcmp.id,
            'standard_price': 200.0,
        })

        # Produto com lote
        self.product_lot = self.env['product.product'].create({
            'name': 'Product Lot PCMP',
            'type': 'product',
            'categ_id': self.category_pcmp.id,
            'tracking': 'lot',
            'lot_valuated': True,
        })

        # Criar warehouse
        self.warehouse = self.env['stock.warehouse'].search([
            ('company_id', '=', self.env.company.id)
        ], limit=1)

        # Criar lote
        self.lot1 = self.env['stock.lot'].create({
            'name': 'LOT-TEST-001',
            'product_id': self.product_lot.id,
        })

    def test_01_stock_initial_without_pcmp(self):
        """Testa que stock inicial sem PCMP configurado gera erro"""
        # Criar stock inicial
        stock_initial = self.env['stock.initial'].create({
            'warehouse_id': self.warehouse.id,
            'date': datetime.now(),
        })

        # Adicionar linha sem PCMP configurado
        line = self.env['stock.initial.line'].create({
            'stock_initial_id': stock_initial.id,
            'product_id': self.product1.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'quantity': 100,
        })

        # Tentar validar deve gerar erro
        with self.assertRaises(ValidationError) as cm:
            stock_initial.action_validate_stock_initial()

        self.assertIn('PCMP inicial não configurado', str(cm.exception))

    def test_02_stock_initial_with_pcmp(self):
        """Testa stock inicial com PCMP configurado"""
        # Criar PCMP inicial
        pcmp1 = self.env['stock.pcmp.initial'].create({
            'product_id': self.product1.id,
            'warehouse_id': self.warehouse.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'initial_pcmp': 110.0,
            'initial_stock': 0,
            'year': str(datetime.now().year),
            'state': 'confirmed',
        })

        pcmp2 = self.env['stock.pcmp.initial'].create({
            'product_id': self.product2.id,
            'warehouse_id': self.warehouse.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'initial_pcmp': 220.0,
            'initial_stock': 0,
            'year': str(datetime.now().year),
            'state': 'confirmed',
        })

        # Criar stock inicial
        stock_initial = self.env['stock.initial'].create({
            'warehouse_id': self.warehouse.id,
            'date': datetime.now(),
        })

        # Adicionar linhas
        line1 = self.env['stock.initial.line'].create({
            'stock_initial_id': stock_initial.id,
            'product_id': self.product1.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'quantity': 50,
        })

        line2 = self.env['stock.initial.line'].create({
            'stock_initial_id': stock_initial.id,
            'product_id': self.product2.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'quantity': 30,
        })

        # Verificar valores calculados
        self.assertEqual(line1.pcmp_unit, 110.0)
        self.assertEqual(line1.subtotal, 50 * 110.0)

        self.assertEqual(line2.pcmp_unit, 220.0)
        self.assertEqual(line2.subtotal, 30 * 220.0)

        # Validar stock inicial
        stock_initial.action_validate_stock_initial()

        # Verificar estado
        self.assertEqual(stock_initial.state, 'validated')

        # Verificar que PCMP inicial está em uso
        pcmp1.refresh()
        pcmp2.refresh()
        self.assertEqual(pcmp1.state, 'used')
        self.assertEqual(pcmp2.state, 'used')

    def test_03_stock_initial_with_lot_pcmp(self):
        """Testa stock inicial com produto que tem lote e PCMP"""
        # Criar PCMP inicial para lote
        pcmp_lot = self.env['stock.pcmp.initial'].create({
            'product_id': self.product_lot.id,
            'lot_id': self.lot1.id,
            'warehouse_id': self.warehouse.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'initial_pcmp': 300.0,
            'initial_stock': 0,
            'year': str(datetime.now().year),
            'state': 'confirmed',
        })

        # Criar stock inicial
        stock_initial = self.env['stock.initial'].create({
            'warehouse_id': self.warehouse.id,
            'date': datetime.now(),
        })

        # Adicionar linha com lote
        line = self.env['stock.initial.line'].create({
            'stock_initial_id': stock_initial.id,
            'product_id': self.product_lot.id,
            'lot_id': self.lot1.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'quantity': 25,
        })

        # Verificar PCMP do lote
        self.assertEqual(line.pcmp_unit, 300.0)

        # Validar
        stock_initial.action_validate_stock_initial()

        # Verificar que o lote tem o PCMP correto
        self.lot1.refresh()
        self.assertEqual(self.lot1.standard_price, 300.0)

    def test_04_stock_initial_validation_pcmp_invalid_state(self):
        """Testa validação com PCMP em estado inválido"""
        # Criar PCMP inicial em rascunho (não confirmado)
        pcmp = self.env['stock.pcmp.initial'].create({
            'product_id': self.product1.id,
            'warehouse_id': self.warehouse.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'initial_pcmp': 100.0,
            'initial_stock': 0,
            'year': str(datetime.now().year),
            'state': 'draft',  # Estado inválido
        })

        # Criar stock inicial
        stock_initial = self.env['stock.initial'].create({
            'warehouse_id': self.warehouse.id,
            'date': datetime.now(),
        })

        # Adicionar linha
        line = self.env['stock.initial.line'].create({
            'stock_initial_id': stock_initial.id,
            'product_id': self.product1.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'quantity': 100,
        })

        # Tentar validar deve gerar erro
        with self.assertRaises(ValidationError) as cm:
            stock_initial.action_validate_stock_initial()

        self.assertIn('PCMP inicial inválido', str(cm.exception))

    def test_05_stock_initial_validation_pcmp_zero(self):
        """Testa validação com PCMP zero"""
        # Criar PCMP inicial com valor zero
        pcmp = self.env['stock.pcmp.initial'].create({
            'product_id': self.product1.id,
            'warehouse_id': self.warehouse.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'initial_pcmp': 0.0,  # PCMP zero
            'initial_stock': 0,
            'year': str(datetime.now().year),
            'state': 'confirmed',
        })

        # Criar stock inicial
        stock_initial = self.env['stock.initial'].create({
            'warehouse_id': self.warehouse.id,
            'date': datetime.now(),
        })

        # Adicionar linha
        line = self.env['stock.initial.line'].create({
            'stock_initial_id': stock_initial.id,
            'product_id': self.product1.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'quantity': 100,
        })

        # Tentar validar deve gerar erro
        with self.assertRaises(ValidationError) as cm:
            stock_initial.action_validate_stock_initial()

        self.assertIn('PCMP inicial inválido', str(cm.exception))
        self.assertIn('PCMP: 0', str(cm.exception))

    def test_06_stock_initial_duplicate_prevention(self):
        """Testa prevenção de duplicação de stock inicial"""
        # Criar PCMP inicial
        pcmp = self.env['stock.pcmp.initial'].create({
            'product_id': self.product1.id,
            'warehouse_id': self.warehouse.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'initial_pcmp': 100.0,
            'initial_stock': 0,
            'year': str(datetime.now().year),
            'state': 'confirmed',
        })

        # Criar primeiro stock inicial
        stock_initial1 = self.env['stock.initial'].create({
            'warehouse_id': self.warehouse.id,
            'date': datetime.now(),
        })

        line1 = self.env['stock.initial.line'].create({
            'stock_initial_id': stock_initial1.id,
            'product_id': self.product1.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'quantity': 100,
        })

        stock_initial1.action_validate_stock_initial()

        # Tentar criar segundo stock inicial para o mesmo período
        stock_initial2 = self.env['stock.initial'].create({
            'warehouse_id': self.warehouse.id,
            'date': datetime.now(),
        })

        line2 = self.env['stock.initial.line'].create({
            'stock_initial_id': stock_initial2.id,
            'product_id': self.product1.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'quantity': 200,
        })

        # Deve permitir criar mas ao validar deve verificar duplicação
        # (depende da lógica de negócio implementada)

    def test_07_stock_initial_multi_location(self):
        """Testa stock inicial com múltiplas localizações"""
        # Criar segunda localização
        location2 = self.env['stock.location'].create({
            'name': 'Test Location 2',
            'usage': 'internal',
            'location_id': self.warehouse.view_location_id.id,
        })

        # Criar PCMP inicial para diferentes localizações
        pcmp1 = self.env['stock.pcmp.initial'].create({
            'product_id': self.product1.id,
            'warehouse_id': self.warehouse.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'initial_pcmp': 100.0,
            'initial_stock': 0,
            'year': str(datetime.now().year),
            'state': 'confirmed',
        })

        pcmp2 = self.env['stock.pcmp.initial'].create({
            'product_id': self.product1.id,
            'warehouse_id': self.warehouse.id,
            'location_id': location2.id,
            'initial_pcmp': 120.0,
            'initial_stock': 0,
            'year': str(datetime.now().year),
            'state': 'confirmed',
        })

        # Criar stock inicial
        stock_initial = self.env['stock.initial'].create({
            'warehouse_id': self.warehouse.id,
            'date': datetime.now(),
        })

        # Adicionar linhas para diferentes localizações
        line1 = self.env['stock.initial.line'].create({
            'stock_initial_id': stock_initial.id,
            'product_id': self.product1.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'quantity': 50,
        })

        line2 = self.env['stock.initial.line'].create({
            'stock_initial_id': stock_initial.id,
            'product_id': self.product1.id,
            'location_id': location2.id,
            'quantity': 30,
        })

        # Verificar que cada linha usa o PCMP correto
        self.assertEqual(line1.pcmp_unit, 100.0)
        self.assertEqual(line2.pcmp_unit, 120.0)

        # Validar
        stock_initial.action_validate_stock_initial()

        self.assertEqual(stock_initial.state, 'validated')