from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from markupsafe import Markup
import logging
import re

_logger = logging.getLogger(__name__)



class ImportDocument(models.Model):
    _name = 'import.document'
    _description = 'Documento de Importação'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin',
        'import.document.actions',
        'import.document.pcmp',
        'import.document.stock',
    ]
    _order = 'date desc, name desc'

    # Identificação
    name = fields.Char(
        string='Referência',
        default='New',
        readonly=True,
        copy=False,
        tracking=True
    )
    date = fields.Date(
        string='Data do Documento',
        default=fields.Date.today,
        required=True,
        tracking=True
    )
    arrival_date = fields.Date(
        string='Data de Chegada',
        tracking=True,
    )
    reception_date = fields.Datetime(
        string='Data/Hora de Recepção',
        readonly=True,
        copy=False,
        tracking=True,
        help='Data e hora exacta da entrada em stock (gerado automaticamente pelo sistema)',
    )

    # Parceiros
    supplier_id = fields.Many2one(
        'res.partner',
        string='Fornecedor',
        required=True,
        tracking=True,
        domain=[
            ('supplier_rank', '>', 0)
        ],
    )
    forwarder_id = fields.Many2one(
        'res.partner',
        string='Despachante',
        tracking=True,
        domain=[
            ('supplier_rank', '>', 0)
        ],
    )
    bank_tc_id = fields.Many2one(
        'res.bank',
        string='Banco TC',
        tracking=True,
        help='Banco que aprovou o Termo de Compromisso (TC) da importação'
    )

    # Armazém e Empresa
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Armazém',
        required=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        default=lambda self: self.env.company,
        required=True,
        readonly=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Moeda',
        related='company_id.currency_id',
        readonly=True,
        store=True
    )

    # Estado
    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('in_transit', 'Em Trânsito'),
        ('partial', 'Recebido Parcialmente'),  # Mercadoria recebida, aguardando custos
        ('done', 'Finalizado'),
        ('cancelled', 'Cancelado')
    ], default='draft', string='Estado', copy=False, tracking=True)

    # Linhas de produtos importados
    import_line_ids = fields.One2many(
        'import.document.line',
        'import_id',
        string='Produtos Importados',
        compute='_compute_import_lines',
        store=True,
        readonly=False,  # Permite ajustes manuais se necessário
    )

    # Linhas de serviços embebidos nas POs de mercadoria/ferramentas
    service_line_ids = fields.One2many(
        'import.document.line.service',
        'import_id',
        string='Serviços nas POs',
        compute='_compute_service_lines',
        store=True,
        readonly=False,
        help='Serviços incluídos nas POs de mercadoria (frete, manuseamento, etc.)'
    )

    # POs relacionadas
    purchase_order_ids = fields.Many2many(
        'purchase.order',
        'import_document_purchase_order_rel',
        'import_document_id',
        'purchase_order_id',
        string='Pedidos de Compra',
        help='Pedidos de compra associados a esta importação'
    )

    available_po_ids = fields.Many2many(
        'purchase.order',
        compute='_compute_available_po_ids',
        string='POs Disponíveis',
        help='Purchase Orders disponíveis (não vinculadas a transformações)'
    )

    # Pickings associados (rastreabilidade)
    picking_ids = fields.Many2many(
        'stock.picking',
        compute='_compute_picking_ids',
        string='Pickings de Recebimento',
        help='Pickings de entrada associados a esta importação'
    )
    picking_count = fields.Integer(
        string='Nº Pickings',
        compute='_compute_picking_ids',
        help='Número de pickings de entrada associados'
    )

    # Valores calculados
    total_product_cost = fields.Monetary(
        string='Custo Mercadoria',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id'
    )
    total_embedded_service_cost = fields.Monetary(
        string='Serviços nas POs',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
        help='Total de serviços incluídos nas POs de mercadoria (frete, manuseamento, etc.)'
    )
    total_service_cost = fields.Monetary(
        string='Custos Adicionais',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
        help='Total de custos adicionais (POs de serviço + serviços nas POs de mercadoria)'
    )
    total_import_cost = fields.Monetary(
        string='Custo Total Importação',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id'
    )

    # Campos PCMP
    pcmp_calculation_date = fields.Datetime(
        string='Data Cálculo PCMP',
        readonly=True
    )
    pcmp_adjusted = fields.Boolean(
        string='PCMP Ajustado',
        default=False,
        readonly=True
    )
    stock_received = fields.Boolean(
        string='Stock Recebido',
        default=False,
        readonly=True,
        help='Indica se a entrada provisória de stock já foi feita'
    )

    # Landed Cost associado
    landed_cost_id = fields.Many2one(
        'stock.landed.cost',
        string='Landed Cost',
        readonly=True,
        copy=False,
        help='Landed cost criado para distribuir custos adicionais'
    )

    # ========================================
    # AJUSTE DE CMV (Vendas no período provisório)
    # ========================================
    total_cmv_adjustment = fields.Monetary(
        string='Ajuste CMV',
        currency_field='currency_id',
        readonly=True,
        help='Ajuste de Custo das Mercadorias Vendidas para unidades vendidas durante o período provisório'
    )
    cmv_adjustment_move_id = fields.Many2one(
        'account.move',
        string='Lançamento Ajuste CMV',
        readonly=True,
        copy=False,
        help='Lançamento contabilístico de ajuste de CMV'
    )
    qty_sold_provisional = fields.Float(
        string='Qtd. Vendida (Provisório)',
        compute='_compute_provisional_sales',
        store=True,
        readonly=True,
        help='Total de unidades vendidas durante o período provisório (antes da finalização)'
    )

    # Documentos anexados
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Documentos',
        help='Anexar DU, faturas, etc.'
    )

    # Notas
    notes = fields.Text(string='Notas')

    # Responsáveis
    user_id = fields.Many2one(
        'res.users',
        string='Responsável',
        default=lambda self: self.env.user,
        tracking=True
    )

    @api.depends('state', 'stock_received', 'import_line_ids.qty_sold_provisional')
    def _compute_provisional_sales(self):
        """Calcula total de vendas durante período provisório"""
        for doc in self:
            doc.qty_sold_provisional = sum(doc.import_line_ids.mapped('qty_sold_provisional'))

    @api.depends('purchase_order_ids', 'purchase_order_ids.picking_ids')
    def _compute_picking_ids(self):
        """Computar pickings de entrada das POs de mercadoria"""
        for doc in self:
            product_orders = doc.purchase_order_ids.filtered(lambda po: po.is_product_type)
            pickings = product_orders.mapped('picking_ids').filtered(
                lambda p: p.picking_type_code == 'incoming'
            )
            doc.picking_ids = pickings
            doc.picking_count = len(pickings)

    @api.depends('purchase_order_ids')
    def _compute_available_po_ids(self):
        """Computar POs disponíveis - excluindo vinculadas a transformações"""
        PurchaseOrder = self.env['purchase.order']

        for record in self:
            # Domain base
            domain = [
                ('state', 'in', ['purchase', 'done']),
                ('no_cost_validation', '=', False)
            ]

            # Verificar se campo transformation_document_ids existe (sem criar dependência!)
            if 'transformation_document_ids' in PurchaseOrder._fields:
                domain.append(('transformation_document_ids', '=', False))

            # Buscar POs disponíveis
            available_pos = PurchaseOrder.search(domain)

            # Filtrar importações (permitir próprio doc)
            if 'import_document_ids' in PurchaseOrder._fields:
                available_pos = available_pos.filtered(
                    lambda po: not po.import_document_ids or
                              (len(po.import_document_ids) == 1 and
                               record in po.import_document_ids)
                )

            record.available_po_ids = available_pos

    @api.depends('import_line_ids.subtotal', 'service_line_ids.subtotal',
                 'service_line_ids.is_from_service_po', 'purchase_order_ids.order_line.price_subtotal')
    def _compute_totals(self):
        """
        Calcula totais (todos os valores já em moeda da empresa).

        - Produtos: subtotal das linhas (via stock.move.price_unit, já convertido)
        - Serviços: subtotal de TODAS as linhas em service_line_ids
        - Total custos adicionais: soma dos subtotais das linhas de serviço

        IMPORTANTE: Usa service_line_ids (já convertidos) em vez de amount_total_cc
        para garantir consistência com o Landed Cost (que usa price_subtotal sem impostos).
        """
        for doc in self:
            # Custo dos produtos - já em moeda empresa
            doc.total_product_cost = sum(doc.import_line_ids.mapped('subtotal'))

            # FIX BUG 1: Somar TODAS as linhas de serviço exibidas na view
            # (tanto embebidas quanto de POs de serviço)
            doc.total_embedded_service_cost = sum(doc.service_line_ids.mapped('subtotal'))

            # FIX BUG 2: Total de custos adicionais = soma das linhas de serviço
            # Isto garante consistência com o Landed Cost (que usa price_subtotal sem impostos)
            doc.total_service_cost = doc.total_embedded_service_cost

            # Total
            doc.total_import_cost = doc.total_product_cost + doc.total_service_cost

    @api.depends('purchase_order_ids',
                 'purchase_order_ids.picking_ids.move_ids',
                 'purchase_order_ids.picking_ids.move_ids.quantity',
                 'purchase_order_ids.picking_ids.move_ids.product_id',
                 'state',
                 'stock_received')
    def _compute_import_lines(self):
        """
        Auto-sincroniza linhas com stock.move dos pickings (REFATORADO).

        IMPORTANTE:
        - Só recalcula em estados 'draft' e 'in_transit'
        - Após receber stock (partial/received), linhas ficam congeladas
        - Preserva ajustes manuais de custos quando possível
        - USA stock.move diretamente em vez de stock.move.line
        """
        for doc in self:
            # SÓ recalcula em draft ou in_transit
            if doc.state not in ['draft', 'in_transit']:
                continue

            # Se já recebeu stock, não mexer!
            if doc.stock_received:
                _logger.info(f"⚠️ Doc {doc.name}: Stock já recebido, não recalculando linhas")
                continue

            # Se já tem custos distribuídos, não mexer!
            if any(line.landed_cost > 0 for line in doc.import_line_ids):
                _logger.info(f"⚠️ Doc {doc.name}: Já tem custos distribuídos, não recalculando linhas")
                continue

            # Se não tem POs, limpar linhas
            product_orders = doc.purchase_order_ids.filtered(lambda po: po.is_product_type)
            if not product_orders:
                doc.import_line_ids = [(5, 0, 0)]
                _logger.info(f"🧹 Doc {doc.name}: Sem POs de mercadoria - linhas limpas")
                continue

            # Buscar pickings
            pickings = product_orders.mapped('picking_ids').filtered(
                lambda p: p.state in ['assigned', 'done'] and p.picking_type_code == 'incoming'
            )

            if not pickings:
                _logger.warning(f"⚠️ Doc {doc.name}: POs sem pickings em assigned/done")
                continue

            _logger.info(f"📋 Doc {doc.name}: Sincronizando com {len(pickings)} pickings")

            # Preservar dados manuais (se existirem)
            manual_data = {}
            for line in doc.import_line_ids:
                if line.stock_move_id:
                    manual_data[line.stock_move_id.id] = {
                        'description': line.description,
                        'purchase_order_line_id': line.purchase_order_line_id.id if line.purchase_order_line_id else False,
                    }

            # Criar novas linhas a partir dos stock.move
            lines_to_create = []
            sequence = 10
            used_move_ids = set()

            for picking in pickings:
                for move in picking.move_ids:
                    # Evitar duplicatas
                    if move.id in used_move_ids:
                        continue
                    used_move_ids.add(move.id)

                    # Criar linha baseada no stock.move
                    line_vals = {
                        'sequence': sequence,
                        'product_id': move.product_id.id,
                        'quantity': move.product_uom_qty,
                        'unit_price_po': move.purchase_line_id.price_unit,
                        'unit_price': move.price_unit,
                        'stock_move_id': move.id,
                    }

                    # Restaurar dados manuais se existirem
                    if move.id in manual_data:
                        line_vals.update(manual_data[move.id])
                    else:
                        line_vals['description'] = move.name
                        line_vals['purchase_order_line_id'] = move.purchase_line_id.id if move.purchase_line_id else False

                    lines_to_create.append((0, 0, line_vals))
                    sequence += 10

            # Substituir todas as linhas
            if lines_to_create:
                doc.import_line_ids = [(5, 0, 0)] + lines_to_create
                _logger.info(f"✅ Doc {doc.name}: {len(lines_to_create)} linhas sincronizadas")
            else:
                _logger.warning(f"⚠️ Doc {doc.name}: Nenhuma linha criada dos pickings")

    @api.depends('purchase_order_ids', 'purchase_order_ids.order_line',
                 'purchase_order_ids.order_line.product_id',
                 'state', 'stock_received')
    def _compute_service_lines(self):
        """
        Sincroniza linhas de serviço de TODAS as POs:
        1. Serviços embebidos em POs de mercadoria (is_from_service_po=False)
        2. Linhas de POs de serviço puras (is_from_service_po=True)

        MULTI-MOEDA: Converte unit_price para moeda da empresa, guarda original em unit_price_po
        """
        for doc in self:
            # SÓ recalcula em draft, in_transit ou partial
            # Em partial: pode adicionar POs de serviço (despachante, frete)
            if doc.state not in ['draft', 'in_transit', 'partial']:
                continue

            service_lines_to_create = []
            sequence = 10

            # 1. POs de mercadoria e similares (serviços embebidos)
            product_orders = doc.purchase_order_ids.filtered(
                lambda po: po.is_product_type
            )

            # Data de conversão: reception_date (definitiva) ou date_order (provisória)
            convert_date = doc.reception_date.date() if doc.reception_date else None

            for po in product_orders:
                po_fallback_date = po.date_order.date() if po.date_order else fields.Date.today()
                for line in po.order_line:
                    # Só linhas de serviço com land_cost_ok = True
                    if line.product_id and line.product_id.type == 'service' and line.product_id.landed_cost_ok:
                        # Converter unit_price para moeda empresa
                        if po.currency_id and po.currency_id != doc.currency_id:
                            converted_price = po.currency_id._convert(
                                line.price_unit,
                                doc.currency_id,
                                doc.company_id,
                                convert_date or po_fallback_date
                            )
                            # Hist: sempre com taxa da date_order (preço original convertido)
                            converted_unit_price_hist = po.currency_id._convert(
                                line.price_unit,
                                doc.currency_id,
                                doc.company_id,
                                po_fallback_date
                            )
                        else:
                            converted_price = line.price_unit
                            converted_unit_price_hist = line.price_unit

                        service_lines_to_create.append((0, 0, {
                            'sequence': sequence,
                            'product_id': line.product_id.id,
                            'description': line.name,
                            'quantity': line.product_qty,
                            'unit_price': converted_price,  # Moeda empresa
                            'unit_price_po': line.price_unit,  # Moeda original PO
                            'unit_price_hist': converted_unit_price_hist,  # Preço original convertido (taxa date_order)
                            'purchase_order_line_id': line.id,
                            'is_from_service_po': False,  # Serviço embebido
                        }))
                        sequence += 10

            # 2. POs de serviço puras (freight, customs, etc.)
            service_orders = doc.purchase_order_ids.filtered(
                lambda po: not po.is_product_type
            )

            for po in service_orders:
                po_fallback_date = po.date_order.date() if po.date_order else fields.Date.today()
                for line in po.order_line:
                    # Só linhas com land_cost_ok = True
                    if line.product_id and line.product_id.type == 'service' and line.product_id.landed_cost_ok:
                        # Converter unit_price para moeda empresa
                        if po.currency_id and po.currency_id != doc.currency_id:
                            converted_price = po.currency_id._convert(
                                line.price_unit,
                                doc.currency_id,
                                doc.company_id,
                                convert_date or po_fallback_date
                            )
                            # Hist: sempre com taxa da date_order (preço original convertido)
                            converted_unit_price_hist = po.currency_id._convert(
                                line.price_unit,
                                doc.currency_id,
                                doc.company_id,
                                po_fallback_date
                            )
                        else:
                            converted_price = line.price_unit
                            converted_unit_price_hist = line.price_unit

                        service_lines_to_create.append((0, 0, {
                            'sequence': sequence,
                            'product_id': line.product_id.id,
                            'description': line.name,
                            'quantity': line.product_qty,
                            'unit_price': converted_price,  # Moeda empresa
                            'unit_price_po': line.price_unit,  # Moeda original PO
                            'unit_price_hist': converted_unit_price_hist,  # Preço original convertido (taxa date_order)
                            'purchase_order_line_id': line.id,
                            'is_from_service_po': True,  # PO de serviço
                        }))
                        sequence += 10

            # Substituir todas as linhas de serviço
            doc.service_line_ids = [(5, 0, 0)] + service_lines_to_create
            _logger.info(f"✅ Doc {doc.name}: {len(service_lines_to_create)} linhas de serviço sincronizadas (embebidas + POs serviço)")

    @api.constrains('purchase_order_ids')
    def _check_po_exclusivity(self):
        """Validar que PO não está em documento de transformação ou outra importação"""
        for doc in self:
            for po in doc.purchase_order_ids:
                # Verificar se PO está em documento de transformação
                # Usa hasattr para não criar dependência!
                if hasattr(po, 'transformation_document_ids') and po.transformation_document_ids:
                    transformation_doc = po.transformation_document_ids[0]
                    raise ValidationError(
                        f"❌ Pedido de Compra {po.name} já está associado a um Documento de Transformação!\n\n"
                        f"Documento: {transformation_doc.name}\n"
                        f"Estado: {transformation_doc.state}\n\n"
                        f"Cada PO só pode estar em um documento (importação OU transformação)."
                    )

                # Verificar se PO está em outro documento de importação
                other_imports = self.search([
                    ('id', '!=', doc.id if doc.id else 0),
                    ('purchase_order_ids', 'in', po.id)
                ])
                if other_imports:
                    raise ValidationError(
                        f"❌ Pedido de Compra {po.name} já está associado a outro Documento de Importação!\n\n"
                        f"Documento: {other_imports[0].name}\n"
                        f"Estado: {other_imports[0].state}\n\n"
                        f"Cada PO só pode estar em um documento de importação."
                    )

    def _get_last_picking_date_done(self):
        """
        Retorna o date_done do último picking validado das POs de mercadoria.
        Usado para preencher reception_date automaticamente.
        """
        self.ensure_one()
        product_orders = self.purchase_order_ids.filtered(lambda po: po.is_product_type)
        pickings = product_orders.mapped('picking_ids').filtered(
            lambda p: p.state == 'done' and p.date_done
        )
        if pickings:
            return max(pickings.mapped('date_done'))
        return fields.Datetime.now()

    @api.constrains('date', 'arrival_date', 'reception_date')
    def _check_dates(self):
        """
        P2.4 FIX: Validar datas lógicas
        """
        for doc in self:
            today = fields.Date.today()

            # Data do documento não pode ser futura
            if doc.date and doc.date > today:
                raise ValidationError(
                    f"❌ Data do documento não pode ser futura!\n\n"
                    f"Data informada: {doc.date}\n"
                    f"Data atual: {today}"
                )

            # arrival_date deve ser >= date
            if doc.arrival_date and doc.date and doc.arrival_date < doc.date:
                raise ValidationError(
                    f"❌ Data de chegada não pode ser anterior à data do documento!\n\n"
                    f"Data documento: {doc.date}\n"
                    f"Data chegada: {doc.arrival_date}"
                )

            # reception_date deve ser >= arrival_date
            # reception_date é Datetime, comparar só a parte Date
            reception_date_only = doc.reception_date.date() if doc.reception_date else None
            if reception_date_only and doc.arrival_date and reception_date_only < doc.arrival_date:
                raise ValidationError(
                    f"❌ Data de recepção não pode ser anterior à data de chegada!\n\n"
                    f"Data chegada: {doc.arrival_date}\n"
                    f"Data recepção: {reception_date_only}"
                )

    @api.constrains('warehouse_id', 'company_id')
    def _check_warehouse_company(self):
        """
        P2.9 FIX: Validar que warehouse pertence à company
        """
        for doc in self:
            if doc.warehouse_id and doc.company_id:
                if doc.warehouse_id.company_id != doc.company_id:
                    raise ValidationError(
                        f"❌ Armazém '{doc.warehouse_id.name}' não pertence à empresa '{doc.company_id.name}'!\n\n"
                        f"Armazém pertence a: {doc.warehouse_id.company_id.name}\n"
                        f"Documento pertence a: {doc.company_id.name}"
                    )


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Apenas definir 'New' se não tiver nome, não gerar sequência
            if not vals.get('name'):
                vals['name'] = 'New'
        return super().create(vals_list)

    def unlink(self):
        """Bloquear eliminação de documentos de importação"""
        raise UserError(
            _("❌ Não é permitido eliminar Documentos de Importação!\n\n"
              "💡 Solução:\n"
              "Use o botão 'Cancelar' para anular o documento.")
        )

    # ===== Onchange Methods =====

    def action_refresh_lines(self):
        """
        Ação manual para forçar atualização das linhas.
        Útil quando pickings foram modificados e usuário quer sincronizar imediatamente.
        """
        self.ensure_one()

        if self.state not in ['draft', 'in_transit']:
            raise UserError(
                "Só pode atualizar linhas em estado Rascunho ou Em Trânsito.\n\n"
                "Após receber mercadoria, as linhas ficam congeladas."
            )

        if self.stock_received:
            raise UserError(
                "Stock já foi recebido!\n\n"
                "Não é possível atualizar linhas após entrada de stock."
            )

        if any(line.landed_cost > 0 for line in self.import_line_ids):
            raise UserError(
                "Já existem custos distribuídos!\n\n"
                "Não é possível atualizar linhas após distribuição de custos."
            )

        # Forçar recálculo
        self.with_context(force_compute=True)._compute_import_lines()

        # Contar linhas criadas
        line_count = len(self.import_line_ids)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '✅ Linhas Atualizadas',
                'message': f'{line_count} linhas sincronizadas com os pickings atuais.',
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    @api.onchange('purchase_order_ids')
    def _onchange_purchase_order_ids(self):
        """
        Validação imediata na UI quando altera POs em estado partial
        Melhor UX - feedback instantâneo sem precisar salvar
        """
        if self.state == 'partial' and self._origin and self._origin.id:
            # POs de mercadoria originais (IDs)
            original_product_po_ids = set(
                self._origin.purchase_order_ids.filtered(
                    lambda po: po.is_product_type
                ).ids
            )

            # POs de mercadoria atuais (IDs)
            current_product_po_ids = set(
                self.purchase_order_ids.filtered(
                    lambda po: po.is_product_type
                ).ids
            )

            # Detectar remoções por IDs
            removed_product_po_ids = original_product_po_ids - current_product_po_ids
            if removed_product_po_ids:
                # Obter nomes das POs removidas
                removed_pos = self.env['purchase.order'].browse(list(removed_product_po_ids))

                # Reverter alteração - manter POs originais + novas de serviço
                service_pos = self.purchase_order_ids.filtered(
                    lambda po: not po.is_product_type
                )
                original_product_pos = self._origin.purchase_order_ids.filtered(
                    lambda po: po.is_product_type
                )
                self.purchase_order_ids = original_product_pos | service_pos

                return {
                    'warning': {
                        'title': '⚠️ Operação Bloqueada',
                        'message': (
                            'Não pode remover POs de Mercadoria após recepção parcial!\n\n'
                            f'Tentou remover: {", ".join(removed_pos.mapped("name"))}\n\n'
                            'O stock destas POs já foi recebido no armazém.\n'
                            'Apenas POs de serviços (frete, impostos) podem ser alteradas.'
                        )
                    }
                }

            # Detectar adições por IDs
            added_product_po_ids = current_product_po_ids - original_product_po_ids
            if added_product_po_ids:
                # Obter nomes das POs adicionadas
                added_pos = self.env['purchase.order'].browse(list(added_product_po_ids))

                # Reverter alteração - manter apenas POs originais de produto
                service_pos = self.purchase_order_ids.filtered(
                    lambda po: not po.is_product_type
                )
                original_product_pos = self._origin.purchase_order_ids.filtered(
                    lambda po: po.is_product_type
                )
                self.purchase_order_ids = original_product_pos | service_pos

                return {
                    'warning': {
                        'title': '⚠️ Operação Bloqueada',
                        'message': (
                            'Não pode adicionar novas POs de Mercadoria após recepção parcial!\n\n'
                            f'Tentou adicionar: {", ".join(added_pos.mapped("name"))}\n\n'
                            'O stock já foi recebido com base nas POs existentes.\n'
                            'Apenas POs de serviços (frete, impostos) podem ser adicionadas.'
                        )
                    }
                }

    def write(self, vals):
        """
        Override write para validar alterações em POs quando em estado partial
        e proteger custos finalizados contra alterações
        """
        # 1. PROTEÇÃO: Impedir alteração de custos após finalização (state='done')
        cost_fields = ['import_line_ids']  # Linhas contêm os custos
        if any(field in vals for field in cost_fields):
            for doc in self.filtered(lambda d: d.state == 'done'):
                # Verificar se está tentando alterar custos nas linhas
                if 'import_line_ids' in vals:
                    # Comandos Many2many: (1, id, vals) = update
                    for command in vals.get('import_line_ids', []):
                        # command[0] == 1 significa update de linha existente
                        if command[0] == 1:
                            line_vals = command[2] if len(command) > 2 else {}
                            # Campos de custo que não podem ser alterados
                            protected_fields = ['final_unit_cost', 'pcmp_calculated', 'landed_cost',
                                               'unit_price', 'unit_price_validated', 'quantity']

                            if any(f in line_vals for f in protected_fields):
                                raise UserError(
                                    f"❌ Não pode alterar custos após finalização!\n\n"
                                    f"Documento: {doc.name}\n"
                                    f"Estado: Finalizado\n\n"
                                    f"💡 Custos finalizados são imutáveis para garantir integridade do PCMP.\n"
                                    f"Se precisar corrigir valores, cancele o documento e crie um novo."
                                )

        # 2. Se está alterando purchase_order_ids e está em estado partial
        if 'purchase_order_ids' in vals:
            for doc in self.filtered(lambda d: d.state == 'partial'):
                # Obter POs de mercadoria atuais
                current_product_pos = doc.purchase_order_ids.filtered(
                    lambda po: po.is_product_type
                )

                # Processar comandos Many2many
                for command in vals.get('purchase_order_ids', []):
                    # command[0] = operação: 2=remove, 3=unlink, 4=link, 5=clear, 6=replace
                    if command[0] in [2, 3]:  # Tentando remover
                        po_id = command[1]
                        po = self.env['purchase.order'].browse(po_id)
                        if po.is_product_type:
                            raise UserError(
                                "⚠️ Não pode remover POs de Mercadoria após recepção parcial!\n\n"
                                "O stock desta PO já foi recebido no armazém.\n"
                                "Apenas POs de serviços (frete, impostos) podem ser alteradas."
                            )

                    elif command[0] == 4:  # Tentando adicionar
                        po_id = command[1]
                        po = self.env['purchase.order'].browse(po_id)
                        if po.is_product_type:
                            # Verificar se é uma PO nova (não estava antes)
                            if po.id not in current_product_pos.ids:
                                raise UserError(
                                    "⚠️ Não pode adicionar novas POs de Mercadoria após recepção parcial!\n\n"
                                    "O stock já foi recebido com base nas POs existentes.\n"
                                    "Apenas POs de serviços (frete, impostos) podem ser adicionadas."
                                )

                    elif command[0] == 6:  # Replace (substitui tudo)
                        new_po_ids = command[2]
                        new_pos = self.env['purchase.order'].browse(new_po_ids)
                        new_product_pos = new_pos.filtered(lambda p: p.is_product_type)

                        # Verificar se alguma PO de produto foi removida
                        removed_product_pos = current_product_pos - new_product_pos
                        if removed_product_pos:
                            raise UserError(
                                "⚠️ Não pode remover POs de Mercadoria após recepção parcial!\n\n"
                                f"Tentou remover: {', '.join(removed_product_pos.mapped('name'))}\n"
                                "Apenas POs de serviços podem ser alteradas."
                            )

                        # Verificar se alguma PO de produto foi adicionada
                        added_product_pos = new_product_pos - current_product_pos
                        if added_product_pos:
                            raise UserError(
                                "⚠️ Não pode adicionar novas POs de Mercadoria após recepção parcial!\n\n"
                                f"Tentou adicionar: {', '.join(added_product_pos.mapped('name'))}\n"
                                "Apenas POs de serviços podem ser adicionadas."
                            )

        return super(ImportDocument, self).write(vals)

    # ===== MÉTODOS DE ACTIONS, PCMP E STOCK =====
    # Movidos para mixins:
    # - import.document.actions (action_confirm, action_receive_*, etc)
    # - import.document.pcmp (_distribute_costs, _create_landed_cost)
    # - import.document.stock (_ensure_stock_move_ids, _create_*_stock_entry, etc)

    def action_view_landed_cost(self):
        """Abrir landed cost associado"""
        self.ensure_one()
        if not self.landed_cost_id:
            raise UserError(_("Nenhum Landed Cost associado a este documento."))
        return {
            'name': _('Landed Cost'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.landed.cost',
            'view_mode': 'form',
            'res_id': self.landed_cost_id.id,
        }

    def action_view_cmv_adjustment(self):
        """Abrir lançamento de ajuste de CMV"""
        self.ensure_one()
        if not self.cmv_adjustment_move_id:
            raise UserError(_("Nenhum ajuste de CMV associado a este documento."))
        return {
            'name': _('Ajuste CMV'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.cmv_adjustment_move_id.id,
        }


class ImportDocumentLine(models.Model):
    _name = 'import.document.line'
    _description = 'Linha do Documento de Importação'
    _order = 'sequence, id'

    import_id = fields.Many2one(
        'import.document',
        string='Importação',
        required=True,
        readonly=True,
        ondelete='cascade'
    )
    sequence = fields.Integer(string='Sequência', default=10, readonly=True)

    # Produto e Lote
    product_id = fields.Many2one(
        'product.product',
        string='Produto',
        related='stock_move_id.product_id',
        readonly=True,
    )

    # Ligação com stock.move (refatorado para usar move diretamente)
    stock_move_id = fields.Many2one(
        'stock.move',
        string='Movimento de Stock',
        help='Movimento de stock associado (em vez de move_line)',
        readonly=True,
    )

    # Campo base_lot_name (nome base do lote do stock.move)
    base_lot_name = fields.Char(
        string='Nome Base do Lote',
        compute='_compute_base_lot_name',
        readonly=True,
        store=True,
        help='Nome base do lote do stock.move (campo lot_name). Representa a hierarquia superior que agrupa múltiplos lotes com mesmas dimensões.'
    )

    description = fields.Text(string='Descrição', readonly=True,)

    # Quantidades
    quantity = fields.Float(
        string='Quantidade',
        digits='Product Unit of Measure',
        compute='_compute_quantity',
        store=True,
        readonly=True,
        help='Quantidade encomendada (product_uom_qty do stock.move)'
    )
    quantity_received = fields.Float(
        string='Qtd. Recebida',
        digits='Product Unit of Measure',
        compute='_compute_quantity_received',
        store=True,
        readonly=True,
        help='Quantidade efectivamente recebida (quantity do stock.move)'
    )
    product_uom = fields.Many2one(
        'uom.uom',
        string='Unidade',
        related='product_id.uom_id',
        readonly=True
    )

    # Custos originais
    unit_price = fields.Monetary(
        string='Preço Unit. (PO)',
        compute='_compute_unit_price',
        store=True,
        currency_field='currency_id',
        readonly=True,
        help='Preço unitário original (taxa da data da PO)',
    )
    unit_price_validated = fields.Monetary(
        string='Preço Unitário (MZN)',
        compute='_compute_unit_price_validated',
        store=True,
        currency_field='currency_id',
        readonly=True,
        help='Preço unitário recalculado com taxa da data de validação (standard Odoo)',
    )
    subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_subtotal',
        store=True,
        readonly=True,
        currency_field='currency_id'
    )

    # Custos distribuídos
    landed_cost = fields.Monetary(
        string='Custo Adicional',
        currency_field='currency_id',
        readonly=True,
        help='Custo adicional distribuído (frete, impostos, etc.)'
    )
    final_unit_cost = fields.Monetary(
        string='Custo Unitário Final',
        currency_field='currency_id',
        readonly=True,
        help='Custo unitário incluindo custos adicionais'
    )

    # PCMP tracking
    pcmp_before = fields.Monetary(
        string='PCMP Anterior',
        currency_field='currency_id',
        readonly=True
    )
    pcmp_calculated = fields.Monetary(
        string='PCMP Calculado',
        currency_field='currency_id',
        readonly=True
    )

    # Ajuste CMV (vendas no período provisório)
    qty_sold_provisional = fields.Float(
        string='Qtd. Vendida (Prov.)',
        readonly=True,
        help='Quantidade vendida durante o período provisório'
    )
    cmv_adjustment = fields.Monetary(
        string='Ajuste CMV',
        currency_field='currency_id',
        readonly=True,
        help='Ajuste de CMV = (PCMP definitivo - PCMP provisório) × Qtd. vendida'
    )

    # Moeda
    currency_id = fields.Many2one(
        'res.currency',
        related='import_id.currency_id',
        readonly=True,
        store=True
    )
    company_id = fields.Many2one(
        'res.company',
        related='import_id.company_id',
        readonly=True,
        store=True
    )
    
    purchase_order_line_id = fields.Many2one(
        'purchase.order.line',
        string='Linha PO',
        readonly=True,
        help='Linha do pedido de compra original'
    )

    # Campos informativos para moeda original da PO
    po_currency_id = fields.Many2one(
        'res.currency',
        string='Moeda PO',
        compute='_compute_po_currency',
        store=True,
        help='Moeda original da PO'
    )
    unit_price_po = fields.Monetary(
        string='Preço Unitário',
        compute='_compute_unit_price_po',
        store=True,
        currency_field='po_currency_id',
        help='Preço na moeda original da PO'
    )

    @api.depends('purchase_order_line_id.order_id.currency_id')
    def _compute_po_currency(self):
        for line in self:
            line.po_currency_id = line.purchase_order_line_id.order_id.currency_id if line.purchase_order_line_id else False

    @api.depends('purchase_order_line_id.price_unit')
    def _compute_unit_price_po(self):
        for line in self:
            line.unit_price_po = line.purchase_order_line_id.price_unit if line.purchase_order_line_id else 0

    @api.depends('quantity', 'unit_price_validated')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price_validated

    @api.constrains('quantity', 'unit_price_validated', 'final_unit_cost')
    def _check_positive_values(self):
        """
        P2.3 FIX: Validar valores positivos
        """
        for line in self:
            # Quantidade deve ser positiva
            if line.quantity <= 0:
                raise ValidationError(
                    f"❌ Quantidade deve ser positiva!\n\n"
                    f"Produto: {line.product_id.name}\n"
                    f"Quantidade: {line.quantity}"
                )

            # Preço unitário não pode ser negativo
            if line.unit_price_validated < 0:
                raise ValidationError(
                    f"❌ Preço unitário não pode ser negativo!\n\n"
                    f"Produto: {line.product_id.name}\n"
                    f"Preço: {line.unit_price_validated}"
                )

            # Custo final também não pode ser negativo
            if line.final_unit_cost and line.final_unit_cost < 0:
                raise ValidationError(
                    f"❌ Custo final não pode ser negativo!\n\n"
                    f"Produto: {line.product_id.name}\n"
                    f"Custo final: {line.final_unit_cost}"
                )


    @api.depends('stock_move_id.lot_name')
    def _compute_base_lot_name(self):
        """
        Buscar lot_name do stock.move (campo lot_name que contém o nome base).
        """
        for line in self:
            line.base_lot_name = line.stock_move_id.lot_name if line.stock_move_id else ''

    @api.depends('stock_move_id.quantity')
    def _compute_quantity(self):
        """
        Buscar product_uom_qty do stock.move (quantidade encomendada).
        """
        for line in self:
            line.quantity = line.stock_move_id.product_uom_qty if line.stock_move_id else 0

    @api.depends('stock_move_id.quantity')
    def _compute_quantity_received(self):
        """
        Buscar quantity do stock.move (quantidade efectivamente recebida).
        """
        for line in self:
            line.quantity_received = line.stock_move_id.quantity if line.stock_move_id else 0

    @api.depends('stock_move_id.price_unit')
    def _compute_unit_price(self):
        """
        Buscar price_unit do stock.move (já convertido para moeda da empresa pelo Odoo).
        O stock.move.price_unit é preenchido via _get_stock_move_price_unit() da PO line,
        que converte automaticamente da moeda da PO para a moeda da empresa.
        NOTA: Este valor usa a taxa da data da PO (referência).
        """
        for line in self:
            line.unit_price = line.stock_move_id.price_unit if line.stock_move_id else 0

    @api.depends('stock_move_id', 'stock_move_id.purchase_line_id', 'po_currency_id', 'import_id.reception_date')
    def _compute_unit_price_validated(self):
        """
        Preço unitário na moeda da empresa (MZN).
        - Se moeda PO = moeda empresa: move.price_unit directo
        - Se moeda diferente (ex: EUR→MZN): converte com taxa da data de recepção
        """
        for line in self:
            move = line.stock_move_id
            if move and move.purchase_line_id:
                po_currency = line.po_currency_id
                company_currency = line.currency_id
                if not po_currency or po_currency == company_currency:
                    line.unit_price_validated = abs(move.price_unit)
                else:
                    # Converter preço PO para moeda empresa com taxa da recepção
                    reception_date = line.import_id.reception_date or fields.Datetime.now()
                    price_po = line.purchase_order_line_id.price_unit
                    converted = abs(po_currency._convert(
                        price_po, company_currency,
                        line.import_id.company_id, reception_date.date(), round=False
                    ))
                    line.unit_price_validated = converted
                    rate = converted / price_po if price_po else 0
                    source = 'Data Recepção' if line.import_id.reception_date else 'Data Actual'
                    _logger.info(
                        f"💱 unit_price_validated [{line.import_id.name}] "
                        f"{line.product_id.default_code} - {line.base_lot_name}: "
                        f"{price_po:,.2f} {po_currency.name} × {rate:,.4f} = {converted:,.2f} {company_currency.name} "
                        f"({source}: {reception_date.date()})"
                    )
                    # TODO: message_post não funciona dentro de compute (registo pode não estar gravado)
                    # Mover para action_receive_with_costs / action_finalize_provisional
                    # line.import_id.message_post(
                    #     body=Markup(
                    #         "💱 <b>Conversão Câmbio</b><br/><br/>"
                    #         "Artigo: <b>%s</b><br/>"
                    #         "Preço PO: <b>%s %s</b><br/>"
                    #         "Taxa: <b>%s</b> (%s: %s)<br/>"
                    #         "Preço Validado: <b>%s %s</b>"
                    #     ) % (
                    #         f'{line.product_id.display_name or line.product_id.name} - {line.base_lot_name}',
                    #         f'{price_po:,.2f}', po_currency.name,
                    #         f'{rate:,.4f}', source, reception_date.date(),
                    #         f'{converted:,.2f}', company_currency.name,
                    #     ),
                    #     message_type='notification',
                    #     subtype_xmlid='mail.mt_note',
                    # )
            elif move and move.price_unit:
                line.unit_price_validated = abs(move.price_unit)
            else:
                line.unit_price_validated = 0
    

    @api.model_create_multi
    def create(self, vals_list):
        """
        CRÍTICO: Preencher stock_move_id antes de criar.
        """
        for vals in vals_list:
            # Se não tem stock_move_id, buscar via purchase_order_line_id
            _logger.info(f"✅ CREATE vals: %s", vals)

        return super().create(vals_list)


class ImportDocumentLineService(models.Model):
    """Linhas de serviço em POs de mercadoria/ferramentas.

    Representa custos adicionais embebidos nas POs de produtos físicos,
    como frete, manuseamento, etc. incluídos na mesma PO.
    """
    _name = 'import.document.line.service'
    _description = 'Linha de Serviço do Documento de Importação'
    _order = 'sequence, id'

    import_id = fields.Many2one(
        'import.document',
        string='Importação',
        required=True,
        readonly=True,
        ondelete='cascade'
    )
    sequence = fields.Integer(string='Sequência', default=10, readonly=True)

    # Produto (serviço)
    product_id = fields.Many2one(
        'product.product',
        string='Serviço',
        required=True,
        domain=[('type', '=', 'service')]
    )
    description = fields.Char(
        string='Descrição'
    )

    # Quantidades e valores
    quantity = fields.Float(
        string='Quantidade',
        digits='Product Unit of Measure',
        default=1.0
    )
    unit_price = fields.Monetary(
        string='Preço Unitário (MZN)',
        currency_field='currency_id'
    )
    unit_price_hist = fields.Monetary(
        string='Preço Inicial (MZN)',
        currency_field='currency_id',
        readonly=True,
        help='Preço unitário original (taxa da data da PO), guardado para análise',
    )
    subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_subtotal',
        store=True,
        currency_field='currency_id',
        readonly=True
    )

    # Rastreabilidade
    purchase_order_line_id = fields.Many2one(
        'purchase.order.line',
        string='Linha PO',
        help='Linha do pedido de compra original'
    )
    purchase_order_id = fields.Many2one(
        'purchase.order',
        string='Pedido de Compra',
        related='purchase_order_line_id.order_id',
        store=True,
        readonly=True
    )

    # Moeda
    currency_id = fields.Many2one(
        'res.currency',
        related='import_id.currency_id',
        readonly=True,
        store=True
    )

    # Origem da linha
    is_from_service_po = fields.Boolean(
        string='Origem: PO de Serviço',
        default=False,
        store=True,
        help='True se linha vem de PO de serviço (freight, customs, etc.), False se serviço embebido em PO de mercadoria'
    )

    # Campos informativos para moeda original da PO
    po_currency_id = fields.Many2one(
        'res.currency',
        string='Moeda PO',
        compute='_compute_po_currency',
        store=True,
        help='Moeda original da PO'
    )
    unit_price_po = fields.Monetary(
        string='Preço Unitário',
        currency_field='po_currency_id',
        help='Preço na moeda original da PO'
    )

    @api.depends('purchase_order_line_id.order_id.currency_id')
    def _compute_po_currency(self):
        for line in self:
            line.po_currency_id = line.purchase_order_line_id.order_id.currency_id if line.purchase_order_line_id else False

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price