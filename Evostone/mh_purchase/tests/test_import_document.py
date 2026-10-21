from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError
from datetime import datetime


@tagged('post_install', '-at_install')
class TestImportDocument(TransactionCase):
    """
    Testes para Documento de Importação com recálculo PCMP.
    """

    def setUp(self):
        super().setUp()

        # Criar categoria PCMP
        self.category_pcmp = self.env['product.category'].create({
            'name': 'Test PCMP Import Category',
            'property_cost_method': 'pcmp',
            'property_valuation': 'real_time',
        })

        # Criar produtos
        self.product1 = self.env['product.product'].create({
            'name': 'Import Product 1',
            'type': 'product',
            'categ_id': self.category_pcmp.id,
            'standard_price': 100.0,
            'lst_price': 200.0,
        })

        self.product2 = self.env['product.product'].create({
            'name': 'Import Product 2',
            'type': 'product',
            'categ_id': self.category_pcmp.id,
            'standard_price': 150.0,
            'lst_price': 300.0,
        })

        # Criar fornecedor
        self.supplier = self.env['res.partner'].create({
            'name': 'Test Supplier',
            'is_company': True,
            'supplier_rank': 1,
        })

        # Criar despachante
        self.forwarder = self.env['res.partner'].create({
            'name': 'Test Forwarder',
            'is_company': True,
        })

        # Criar tipos de serviço para testes
        area_service = self.env.ref('mh_base.area_service')
        self.service_type_service = self.env['service.type'].create({
            'name': 'Serviço Teste',
            'area_ids': [(6, 0, [area_service.id])],
        })

        # Obter warehouse
        self.warehouse = self.env['stock.warehouse'].search([
            ('company_id', '=', self.env.company.id)
        ], limit=1)

        # Criar PCMP inicial para os produtos
        self.pcmp1 = self.env['stock.pcmp.initial'].create({
            'product_id': self.product1.id,
            'warehouse_id': self.warehouse.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'initial_pcmp': 100.0,
            'initial_stock': 100,
            'year': str(datetime.now().year),
            'state': 'confirmed',
        })

        self.pcmp2 = self.env['stock.pcmp.initial'].create({
            'product_id': self.product2.id,
            'warehouse_id': self.warehouse.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'initial_pcmp': 150.0,
            'initial_stock': 50,
            'year': str(datetime.now().year),
            'state': 'confirmed',
        })

    def test_01_import_document_creation(self):
        """Testa criação básica de documento de importação"""
        import_doc = self.env['import.document'].create({
            'supplier_id': self.supplier.id,
            'forwarder_id': self.forwarder.id,
            'warehouse_id': self.warehouse.id,
            'date': datetime.now(),
        })

        # Verificar sequência
        self.assertNotEqual(import_doc.name, 'New')
        self.assertTrue(import_doc.name.startswith('IMP/'))

        # Adicionar linhas
        line1 = self.env['import.document.line'].create({
            'import_id': import_doc.id,
            'product_id': self.product1.id,
            'quantity': 50,
            'unit_price': 120.0,
        })

        line2 = self.env['import.document.line'].create({
            'import_id': import_doc.id,
            'product_id': self.product2.id,
            'quantity': 30,
            'unit_price': 180.0,
        })

        # Verificar totais
        import_doc._compute_totals()
        self.assertEqual(import_doc.total_product_cost, 50*120 + 30*180)

    def test_02_import_document_workflow(self):
        """Testa workflow completo do documento de importação"""
        import_doc = self.env['import.document'].create({
            'supplier_id': self.supplier.id,
            'warehouse_id': self.warehouse.id,
        })

        # Adicionar produtos
        line = self.env['import.document.line'].create({
            'import_id': import_doc.id,
            'product_id': self.product1.id,
            'quantity': 100,
            'unit_price': 110.0,
        })

        # Estado inicial
        self.assertEqual(import_doc.state, 'draft')

        # Confirmar → Em Trânsito
        import_doc.action_confirm()
        self.assertEqual(import_doc.state, 'in_transit')

        # Receber mercadoria
        import_doc.action_receive()
        self.assertEqual(import_doc.state, 'received')
        self.assertIsNotNone(import_doc.reception_date)

        # Calcular custos (sem custos adicionais)
        import_doc.action_calculate_costs()
        self.assertEqual(import_doc.state, 'costing')
        self.assertEqual(line.final_unit_cost, 110.0)  # Sem custos adicionais

        # Calcular PCMP
        import_doc.action_calculate_pcmp()
        self.assertEqual(import_doc.state, 'calc_pcmp')
        self.assertTrue(import_doc.pcmp_adjusted)

        # Verificar PCMP calculado
        self.assertGreater(line.pcmp_calculated, 0)

        # Finalizar
        import_doc.action_done()
        self.assertEqual(import_doc.state, 'done')

    def test_03_import_with_landed_costs(self):
        """Testa importação com custos adicionais (frete, impostos)"""
        import_doc = self.env['import.document'].create({
            'supplier_id': self.supplier.id,
            'warehouse_id': self.warehouse.id,
        })

        # Produtos importados
        line1 = self.env['import.document.line'].create({
            'import_id': import_doc.id,
            'product_id': self.product1.id,
            'quantity': 100,
            'unit_price': 100.0,  # 10,000 total
        })

        line2 = self.env['import.document.line'].create({
            'import_id': import_doc.id,
            'product_id': self.product2.id,
            'quantity': 50,
            'unit_price': 200.0,  # 10,000 total
        })

        # Criar PO de frete
        po_freight = self.env['purchase.order'].create({
            'partner_id': self.forwarder.id,
            'service_type_id': self.service_type_service.id,
        })

        freight_line = self.env['purchase.order.line'].create({
            'order_id': po_freight.id,
            'product_id': self.env.ref('product.service_delivery', False).id or self.product1.id,
            'name': 'Freight Service',
            'product_qty': 1,
            'price_unit': 2000.0,
        })

        po_freight.button_confirm()
        po_freight.button_done()

        # Criar PO de impostos
        po_customs = self.env['purchase.order'].create({
            'partner_id': self.supplier.id,
            'service_type_id': self.service_type_service.id,
        })

        customs_line = self.env['purchase.order.line'].create({
            'order_id': po_customs.id,
            'product_id': self.env.ref('product.service_delivery', False).id or self.product1.id,
            'name': 'Customs Duties',
            'product_qty': 1,
            'price_unit': 3000.0,
        })

        po_customs.button_confirm()
        po_customs.button_done()

        # Associar POs ao documento (Many2many)
        import_doc.purchase_order_ids = [(6, 0, [po_freight.id, po_customs.id])]

        # Confirmar e receber
        import_doc.action_confirm()
        import_doc.action_receive()

        # Calcular custos
        import_doc.action_calculate_costs()

        # Verificar distribuição de custos
        total_service_cost = 2000.0 + 3000.0  # 5000
        total_product_cost = 20000.0

        # Line 1 deve receber 50% dos custos (10k/20k)
        expected_landed1 = 5000 * 0.5
        self.assertAlmostEqual(line1.landed_cost, expected_landed1, places=2)

        # Line 2 deve receber 50% dos custos
        expected_landed2 = 5000 * 0.5
        self.assertAlmostEqual(line2.landed_cost, expected_landed2, places=2)

        # Verificar custo final unitário
        expected_unit1 = (10000 + expected_landed1) / 100
        self.assertAlmostEqual(line1.final_unit_cost, expected_unit1, places=2)

    def test_04_pcmp_calculation_formula(self):
        """Testa fórmula de cálculo PCMP na importação"""
        # Simular vendas anteriores
        # (Isso afetaria o cálculo PCMP real)

        import_doc = self.env['import.document'].create({
            'supplier_id': self.supplier.id,
            'warehouse_id': self.warehouse.id,
        })

        line = self.env['import.document.line'].create({
            'import_id': import_doc.id,
            'product_id': self.product1.id,
            'quantity': 50,
            'unit_price': 130.0,
        })

        # Workflow até cálculo
        import_doc.action_confirm()
        import_doc.action_receive()
        import_doc.action_calculate_costs()

        # Antes do cálculo PCMP
        old_pcmp = self.product1.standard_price

        # Calcular PCMP
        import_doc.action_calculate_pcmp()

        # Verificar que PCMP foi calculado
        self.assertGreater(line.pcmp_calculated, 0)
        self.assertNotEqual(line.pcmp_calculated, old_pcmp)

        # A fórmula seria:
        # PCMP = [(100×100) - (vendas×100) + (50×130)] / [100 - vendas + 50]
        # Como não há vendas simuladas:
        # PCMP = [(100×100) + (50×130)] / [100 + 50]
        # PCMP = [10000 + 6500] / 150 = 110
        expected_pcmp = (100*100 + 50*130) / (100 + 50)
        self.assertAlmostEqual(line.pcmp_calculated, expected_pcmp, places=2)

    def test_05_import_document_cancellation(self):
        """Testa cancelamento de documento de importação"""
        import_doc = self.env['import.document'].create({
            'supplier_id': self.supplier.id,
            'warehouse_id': self.warehouse.id,
        })

        # Adicionar produto
        line = self.env['import.document.line'].create({
            'import_id': import_doc.id,
            'product_id': self.product1.id,
            'quantity': 100,
            'unit_price': 110.0,
        })

        # Cancelar em rascunho
        import_doc.action_cancel()
        self.assertEqual(import_doc.state, 'cancelled')

        # Voltar a rascunho
        import_doc.action_draft()
        self.assertEqual(import_doc.state, 'draft')

        # Avançar no workflow
        import_doc.action_confirm()
        import_doc.action_receive()

        # Cancelar após recebimento
        import_doc.action_cancel()
        self.assertEqual(import_doc.state, 'cancelled')

        # Não pode cancelar após finalizado
        import_doc2 = self.env['import.document'].create({
            'supplier_id': self.supplier.id,
            'warehouse_id': self.warehouse.id,
        })

        line2 = self.env['import.document.line'].create({
            'import_id': import_doc2.id,
            'product_id': self.product2.id,
            'quantity': 50,
            'unit_price': 160.0,
        })

        import_doc2.action_confirm()
        import_doc2.action_receive()
        import_doc2.action_calculate_costs()
        import_doc2.action_calculate_pcmp()
        import_doc2.action_done()

        with self.assertRaises(UserError):
            import_doc2.action_cancel()

    def test_06_import_with_lots(self):
        """Testa importação com produtos que usam lotes"""
        # Criar produto com lote
        product_lot = self.env['product.product'].create({
            'name': 'Import Product with Lot',
            'type': 'product',
            'categ_id': self.category_pcmp.id,
            'tracking': 'lot',
            'lot_valuated': True,
        })

        # Criar lotes
        lot1 = self.env['stock.lot'].create({
            'name': 'IMP-LOT-001',
            'product_id': product_lot.id,
            'standard_price': 200.0,
        })

        lot2 = self.env['stock.lot'].create({
            'name': 'IMP-LOT-002',
            'product_id': product_lot.id,
            'standard_price': 210.0,
        })

        # Criar PCMP inicial para lotes
        pcmp_lot1 = self.env['stock.pcmp.initial'].create({
            'product_id': product_lot.id,
            'lot_id': lot1.id,
            'warehouse_id': self.warehouse.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'initial_pcmp': 200.0,
            'initial_stock': 50,
            'year': str(datetime.now().year),
            'state': 'confirmed',
        })

        pcmp_lot2 = self.env['stock.pcmp.initial'].create({
            'product_id': product_lot.id,
            'lot_id': lot2.id,
            'warehouse_id': self.warehouse.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'initial_pcmp': 210.0,
            'initial_stock': 30,
            'year': str(datetime.now().year),
            'state': 'confirmed',
        })

        # Criar documento de importação
        import_doc = self.env['import.document'].create({
            'supplier_id': self.supplier.id,
            'warehouse_id': self.warehouse.id,
        })

        # Adicionar linhas com lotes
        line1 = self.env['import.document.line'].create({
            'import_id': import_doc.id,
            'product_id': product_lot.id,
            'lot_id': lot1.id,
            'quantity': 25,
            'unit_price': 220.0,
        })

        line2 = self.env['import.document.line'].create({
            'import_id': import_doc.id,
            'product_id': product_lot.id,
            'lot_id': lot2.id,
            'quantity': 15,
            'unit_price': 230.0,
        })

        # Processar importação
        import_doc.action_confirm()
        import_doc.action_receive()
        import_doc.action_calculate_costs()
        import_doc.action_calculate_pcmp()

        # Verificar PCMP calculado por lote
        self.assertGreater(line1.pcmp_calculated, 0)
        self.assertGreater(line2.pcmp_calculated, 0)
        self.assertNotEqual(line1.pcmp_calculated, line2.pcmp_calculated)

        # Finalizar
        import_doc.action_done()

        # Verificar que lotes foram atualizados
        lot1.refresh()
        lot2.refresh()
        self.assertEqual(lot1.standard_price, line1.pcmp_calculated)
        self.assertEqual(lot2.standard_price, line2.pcmp_calculated)