from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta


@tagged('post_install', '-at_install')
class TestPcmpCalculation(TransactionCase):
    """
    Testes para o cálculo e funcionamento do método PCMP.
    """

    def setUp(self):
        super().setUp()

        # Criar categoria com método PCMP
        self.category_pcmp = self.env['product.category'].create({
            'name': 'Test PCMP Category',
            'property_cost_method': 'pcmp',
            'property_valuation': 'real_time',
        })

        # Criar produto com PCMP
        self.product_pcmp = self.env['product.product'].create({
            'name': 'Test PCMP Product',
            'type': 'product',
            'categ_id': self.category_pcmp.id,
            'standard_price': 100.0,
            'lst_price': 150.0,
        })

        # Criar produto com lote
        self.product_pcmp_lot = self.env['product.product'].create({
            'name': 'Test PCMP Lot Product',
            'type': 'product',
            'categ_id': self.category_pcmp.id,
            'tracking': 'lot',
            'lot_valuated': True,
            'standard_price': 200.0,
        })

        # Criar warehouse
        self.warehouse = self.env['stock.warehouse'].search([
            ('company_id', '=', self.env.company.id)
        ], limit=1)

        # Criar lote
        self.lot = self.env['stock.lot'].create({
            'name': 'LOT001',
            'product_id': self.product_pcmp_lot.id,
            'standard_price': 200.0,
        })

    def test_01_pcmp_initial_creation(self):
        """Testa criação de PCMP inicial"""
        pcmp_initial = self.env['stock.pcmp.initial'].create({
            'product_id': self.product_pcmp.id,
            'warehouse_id': self.warehouse.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'initial_pcmp': 100.0,
            'initial_stock': 50,
            'year': str(datetime.now().year),
        })

        self.assertEqual(pcmp_initial.state, 'draft')

        # Confirmar PCMP inicial
        pcmp_initial.action_confirm()
        self.assertEqual(pcmp_initial.state, 'confirmed')

        # Verificar que não pode criar duplicado
        with self.assertRaises(ValidationError):
            self.env['stock.pcmp.initial'].create({
                'product_id': self.product_pcmp.id,
                'warehouse_id': self.warehouse.id,
                'location_id': self.warehouse.lot_stock_id.id,
                'initial_pcmp': 150.0,
                'initial_stock': 100,
                'year': str(datetime.now().year),
            })

    def test_02_pcmp_initial_with_lot(self):
        """Testa PCMP inicial com lote"""
        pcmp_initial = self.env['stock.pcmp.initial'].create({
            'product_id': self.product_pcmp_lot.id,
            'lot_id': self.lot.id,
            'warehouse_id': self.warehouse.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'initial_pcmp': 250.0,
            'initial_stock': 20,
            'year': str(datetime.now().year),
        })

        pcmp_initial.action_confirm()

        # Verificar que o PCMP está disponível via API
        pcmp_value = self.env['stock.pcmp.initial'].get_pcmp_for_product(
            self.product_pcmp_lot.id,
            lot_id=self.lot.id,
            warehouse_id=self.warehouse.id
        )

        self.assertEqual(pcmp_value, 250.0)

    def test_03_pcmp_cache_functionality(self):
        """Testa funcionamento do cache PCMP"""
        # Criar PCMP inicial
        pcmp_initial = self.env['stock.pcmp.initial'].create({
            'product_id': self.product_pcmp.id,
            'warehouse_id': self.warehouse.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'initial_pcmp': 100.0,
            'initial_stock': 50,
            'year': str(datetime.now().year),
            'state': 'confirmed',
        })

        # Primeira chamada (cria cache)
        value1 = self.env['stock.pcmp.initial'].get_pcmp_for_product_cached(
            self.product_pcmp.id,
            False,  # lot_id
            self.warehouse.id,
            str(datetime.now().year)
        )
        self.assertEqual(value1, 100.0)

        # Modificar valor diretamente no banco (sem invalidar cache)
        self.env.cr.execute("""
            UPDATE stock_pcmp_initial
            SET initial_pcmp = 150.0
            WHERE id = %s
        """, (pcmp_initial.id,))

        # Segunda chamada (deve retornar valor do cache, não o novo)
        value2 = self.env['stock.pcmp.initial'].get_pcmp_for_product_cached(
            self.product_pcmp.id,
            False,
            self.warehouse.id,
            str(datetime.now().year)
        )
        self.assertEqual(value2, 100.0)  # Ainda retorna valor em cache

        # Limpar cache (forma correta no Odoo 18)
        self.env.registry.clear_cache()

        # Terceira chamada (deve buscar novo valor)
        value3 = self.env['stock.pcmp.initial'].get_pcmp_for_product_cached(
            self.product_pcmp.id,
            False,
            self.warehouse.id,
            str(datetime.now().year)
        )
        self.assertEqual(value3, 150.0)  # Agora retorna valor atualizado

    def test_04_product_run_pcmp_method(self):
        """Testa método _run_pcmp do produto"""
        # Para saída (venda)
        value_out = self.product_pcmp._run_pcmp(-10, company=self.env.company)
        self.assertEqual(value_out, 10 * 100.0)  # 10 unidades × 100 (standard_price)

        # Para entrada (não deve recalcular)
        value_in = self.product_pcmp._run_pcmp(20, company=self.env.company)
        self.assertEqual(value_in, 0)  # PCMP não recalcula em entradas

    def test_05_pcmp_lot_synchronization(self):
        """Testa sincronização PCMP do lote"""
        # Alterar standard_price do lote
        old_price = self.lot.standard_price
        self.lot.standard_price = 300.0

        # Verificar que pcmp_value foi sincronizado
        self.assertEqual(self.lot.pcmp_value, 300.0)

        # Verificar que histórico foi criado
        history = self.env['stock.lot.pcmp.history'].search([
            ('lot_id', '=', self.lot.id)
        ], limit=1)

        self.assertTrue(history)
        self.assertEqual(history.old_pcmp, old_price)
        self.assertEqual(history.new_pcmp, 300.0)

    def test_06_pcmp_mixin_calculation(self):
        """Testa cálculo PCMP usando o mixin"""
        PcmpMixin = self.env['pcmp.mixin']

        # Testar cálculo básico
        new_pcmp = PcmpMixin._compute_pcmp_value(
            initial_stock=100,
            initial_pcmp=50.0,
            sales_qty=30,
            current_pcmp=50.0,
            import_qty=50,
            import_cost=60.0
        )

        # Verificar cálculo
        # (100×50 - 30×50 + 50×60) / (100-30+50) = (5000-1500+3000) / 120 = 54.17
        self.assertAlmostEqual(new_pcmp, 54.17, places=2)

    def test_07_pcmp_mixin_edge_cases(self):
        """Testa casos extremos do cálculo PCMP"""
        PcmpMixin = self.env['pcmp.mixin']

        # Caso 1: Denominador zero
        new_pcmp = PcmpMixin._compute_pcmp_value(
            initial_stock=50,
            initial_pcmp=100.0,
            sales_qty=50,
            current_pcmp=100.0,
            import_qty=0,
            import_cost=0
        )
        # Deve retornar current_pcmp quando denominador é 0
        self.assertEqual(new_pcmp, 100.0)

        # Caso 2: Sem vendas
        new_pcmp = PcmpMixin._compute_pcmp_value(
            initial_stock=100,
            initial_pcmp=50.0,
            sales_qty=0,
            current_pcmp=50.0,
            import_qty=50,
            import_cost=70.0
        )
        # (100×50 + 50×70) / (100+50) = 8500 / 150 = 56.67
        self.assertAlmostEqual(new_pcmp, 56.67, places=2)

    def test_08_stock_valuation_layer_pcmp(self):
        """Testa criação de SVL para produtos PCMP"""
        # Criar movimento de saída
        move = self.env['stock.move'].create({
            'name': 'Test PCMP Move',
            'product_id': self.product_pcmp.id,
            'product_uom': self.product_pcmp.uom_id.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
            'product_uom_qty': 5,
        })

        # Confirmar movimento
        move._action_confirm()

        # Verificar price_unit para PCMP
        price_unit = move._get_price_unit()
        self.assertEqual(price_unit, 100.0)  # Deve usar standard_price

    def test_09_pcmp_validation_errors(self):
        """Testa validações e erros PCMP"""
        # Tentar criar PCMP inicial com valor negativo
        with self.assertRaises(ValidationError):
            self.env['stock.pcmp.initial'].create({
                'product_id': self.product_pcmp.id,
                'warehouse_id': self.warehouse.id,
                'location_id': self.warehouse.lot_stock_id.id,
                'initial_pcmp': -100.0,  # Valor negativo
                'initial_stock': 50,
                'year': str(datetime.now().year),
            })

        # Tentar criar com stock negativo
        with self.assertRaises(ValidationError):
            self.env['stock.pcmp.initial'].create({
                'product_id': self.product_pcmp.id,
                'warehouse_id': self.warehouse.id,
                'location_id': self.warehouse.lot_stock_id.id,
                'initial_pcmp': 100.0,
                'initial_stock': -50,  # Stock negativo
                'year': str(datetime.now().year),
            })

    def test_10_pcmp_adjustment_layer(self):
        """Testa criação de layer de ajuste PCMP"""
        # Alterar standard_price do produto
        old_price = self.product_pcmp.standard_price
        self.product_pcmp._change_standard_price(150.0)

        # Verificar que foi criado um layer de ajuste
        adjustment_layer = self.env['stock.valuation.layer'].search([
            ('product_id', '=', self.product_pcmp.id),
            ('is_pcmp_adjustment', '=', True),
            ('quantity', '=', 0),  # Ajuste não tem quantidade
        ], limit=1)

        self.assertTrue(adjustment_layer, "Layer de ajuste PCMP não foi criado")