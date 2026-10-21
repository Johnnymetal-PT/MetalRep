from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError  
from odoo.addons.mh_base.models.purchase_order import PRODUCT_AREA_CODES, PHYSICAL_PRODUCT_CODES

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # Campo service_type e is_import_related estão definidos no módulo mh_base
    # Este módulo adiciona funcionalidade de importação

    import_document_ids = fields.Many2many(
        'import.document',
        'import_document_purchase_order_rel',
        'purchase_order_id',
        'import_document_id',
        string='Documentos de Importação',
        copy=False,
        help='Documentos de importação associados a esta ordem de compra'
    )

    # Subscrever o campo is_import_related do mh_base para adicionar compute
    is_import_related = fields.Boolean(
        compute='_compute_is_import_related',
        store=True
    )
        
    no_cost_validation = fields.Boolean(
        string='Receção Direta (Legado)',
        default=True,
        readonly=True,
        tracking=True,
        copy=False,
        help='Campo legado do antigo fluxo de Documento de Importação. Novas compras usam a receção standard do Odoo.'
    )

    # Controle de peso por contentor
    container_qty = fields.Integer(
        string='Quantidade de Contentores',
        default=1,
        help='Número de contentores para este pedido',
        tracking=True
    )

    total_weight = fields.Float(
        string='Peso Total (KG)',
        compute='_compute_weights',
        store=True,
        digits=(16, 2),
        help='Peso total de todos os produtos'
    )

    weight_per_container = fields.Float(
        string='Peso por Contentor (KG)',
        compute='_compute_weights',
        store=True,
        digits=(16, 2),
        help='Peso médio por contentor (Peso Total / Qtd Contentores)'
    )

    weight_exceeded = fields.Boolean(
        string='Excesso de Peso',
        compute='_compute_weights',
        store=True,
        help='Indica se o peso por contentor excedeu o limite do fornecedor'
    )

    suggested_container_qty = fields.Float(
        string='Contentores Sugeridos',
        compute='_compute_weights',
        store=True,
        digits=(16, 2),
        help='Número mínimo de contentores para não exceder o limite'
    )

    partner_container_max_weight = fields.Float(
        string='Limite por Contentor (KG)',
        compute='_compute_partner_container_max_weight',
        store=True,
        readonly=True,
        digits=(16, 2),
        help='Limite do fornecedor no momento da seleção'
    )

    @api.depends('partner_id')
    def _compute_partner_container_max_weight(self):
        """Capturar limite do fornecedor ao selecionar/alterar parceiro"""
        for order in self:
            if order.partner_id:
                order.partner_container_max_weight = order.partner_id.container_max_weight
            else:
                order.partner_container_max_weight = 0.0

    @api.depends('import_document_ids')
    def _compute_is_import_related(self):
        """Verificar se PO está relacionada com alguma importação"""
        for order in self:
            # Usar o campo Many2many existente para performance
            order.is_import_related = bool(order.import_document_ids)


    @api.depends('order_line.peso', 'container_qty', 'partner_container_max_weight')
    def _compute_weights(self):
        """Calcular pesos e verificar se excedeu limite por contentor.

        total_weight = soma de order_line.peso. As linhas já têm state guard
        próprio (preservam valor quando state in purchase/done), portanto
        somar o snapshot das linhas é equivalente a snapshot do header.
        """
        for order in self:
            total_weight = sum(order.order_line.mapped('peso'))
            order.total_weight = total_weight

            # Peso por contentor
            if order.container_qty > 0:
                order.weight_per_container = total_weight / order.container_qty
            else:
                order.weight_per_container = total_weight

            # Verificar se excedeu o limite do fornecedor
            if order.partner_container_max_weight > 0 and order.container_qty > 0:
                order.weight_exceeded = (
                    order.weight_per_container > order.partner_container_max_weight
                )
            else:
                order.weight_exceeded = False

            # Contentores sugeridos
            if order.partner_container_max_weight > 0:
                order.suggested_container_qty = total_weight / order.partner_container_max_weight
            else:
                order.suggested_container_qty = 0.0

    @api.constrains('service_type_id', 'order_line')
    def _check_service_type_consistency(self):
        """
        Validar consistência entre service_type e linhas.
        Produtos tipo 'service' são sempre permitidos em qualquer PO.
        A validação de product_form aplica-se apenas a produtos stockable/consumable.

        Nota: Só valida quando estado != 'draft' para evitar erros durante edição.
        """
        for order in self:
            # Ignorar validação em rascunho - será validado ao confirmar
            if order.state == 'draft':
                continue

            if not order.order_line:
                continue  # Permite PO sem linhas (rascunho)
            
            area_codes = order._get_area_codes()
            if not area_codes:
                continue
            
            # 1. Artigos devem ter classificação compatível com as áreas
            invalid_lines = order.order_line.filtered(
                lambda l: l.product_id
                and l.product_id.product_classification
                and l.product_id.product_classification not in area_codes
            )
            if invalid_lines:
                products = ', '.join(
                    f"{l.product_id.name} ({l.product_id.product_classification})"
                    for l in invalid_lines
                )
                areas = ', '.join(order.service_type_area_ids.mapped('name'))
                raise ValidationError(
                    f"Pedido de compra '{order.name}':\n"
                    f"Os seguintes artigos não pertencem às áreas de actuação ({areas}):\n"
                    f"{products}"
                )

            # 2. Se o tipo tem áreas de produto, deve ter pelo menos um artigo dessas áreas
            product_areas = area_codes & PRODUCT_AREA_CODES
            if product_areas:
                has_physical = order.order_line.filtered(
                    lambda l: l.product_id
                    and l.product_id.product_classification in product_areas
                )
                if not has_physical:
                    areas = ', '.join(
                        order.service_type_area_ids.filtered(lambda a: a.code in product_areas).mapped('name')
                    )
                    raise ValidationError(
                        f"Pedido de compra '{order.name}':\n"
                        f"Deve ter pelo menos um artigo físico das áreas: {areas}"
                    )

    def button_confirm(self):
        """Confirma a compra pelo fluxo standard, preservando validações locais."""
        orders_to_confirm = self.filtered(lambda order: order.state in ('draft', 'sent'))
        for order in orders_to_confirm:
            if order.partner_id and hasattr(order.partner_id, 'ensure_partner_account'):
                order.partner_id.ensure_partner_account('supplier')

            order._validate_before_confirm()

            lines_without_lot = order.order_line.filtered(
                lambda line: line.lot_name == 'SEM-LOTE'
                and line.product_id
                and line.product_id.tracking in ('lot', 'serial')
            )
            if lines_without_lot:
                products = ', '.join(lines_without_lot.mapped('product_id.name'))
                raise ValidationError(
                    f"Não é possível confirmar o pedido de compra '{order.name}'.\n\n"
                    f"Existem produtos com lote 'SEM-LOTE' que requerem rastreamento:\n"
                    f"{products}\n\n"
                    f"Por favor, defina um lote válido para cada linha antes de confirmar."
                )

            if order._get_area_codes() & PHYSICAL_PRODUCT_CODES and order.weight_exceeded:
                raise ValidationError(
                    f"⚠️ EXCESSO DE PESO NO CONTENTOR\n\n"
                    f"Pedido de compra: {order.name}\n"
                    f"Fornecedor: {order.partner_id.name}\n\n"
                    f"📊 Dados do carregamento:\n"
                    f"• Peso total: {order.total_weight:.2f} KG\n"
                    f"• Quantidade de contentores: {order.container_qty}\n"
                    f"• Peso por contentor: {order.weight_per_container:.2f} KG\n"
                    f"• Limite por contentor: {order.partner_container_max_weight:.2f} KG\n"
                    f"• Excesso: {(order.weight_per_container - order.partner_container_max_weight):.2f} KG\n"
                    f"• Contentores sugeridos: {order.suggested_container_qty:.2f}\n\n"
                    f"❌ O peso por contentor excede o limite permitido pelo fornecedor!\n\n"
                    f"✅ Solução: Aumente a quantidade de contentores ou ajuste as quantidades dos produtos."
                )

        return super().button_confirm()

    def _validate_before_confirm(self):
        """Executa todas as validações antes de confirmar o pedido.

        Chamado pelo button_confirm_final para garantir que as validações
        que foram ignoradas em estado 'draft' são executadas antes de confirmar.
        """
        self.ensure_one()

        # 1. Validar consistência do service_type
        self._validate_service_type_on_confirm()

        # 2. Validar quantidade das linhas
        self.order_line._validate_quantity_positive()

        # 3. Validar dimensões das linhas (se o módulo mh_picking estiver instalado)
        if hasattr(self.order_line, '_validate_dimensions'):
            self.order_line._validate_dimensions()
            
            
    def _validate_service_type_on_confirm(self):
        """Validação de consistência tipo de serviço (chamada ao confirmar)"""
        if not self.order_line:
            return

        area_codes = self._get_area_codes()
        if not area_codes:
            return

        # 1. Artigos devem ter classificação compatível com as áreas
        invalid_lines = self.order_line.filtered(
            lambda l: l.product_id
            and l.product_id.product_classification
            and l.product_id.product_classification not in area_codes
        )
        if invalid_lines:
            products = ', '.join(
                f"{l.product_id.name} ({l.product_id.product_classification})"
                for l in invalid_lines
            )
            areas = ', '.join(self.service_type_area_ids.mapped('name'))
            raise ValidationError(
                f"Pedido de compra '{self.name}':\n"
                f"Os seguintes artigos não pertencem às áreas de actuação ({areas}):\n"
                f"{products}"
            )

        # 2. Se o tipo tem áreas de produto, deve ter pelo menos um artigo dessas áreas
        product_areas = area_codes & PRODUCT_AREA_CODES
        if product_areas:
            has_physical = self.order_line.filtered(
                lambda l: l.product_id
                and l.product_id.product_classification in product_areas
            )
            if not has_physical:
                areas = ', '.join(
                    self.service_type_area_ids.filtered(lambda a: a.code in product_areas).mapped('name')
                )
                raise ValidationError(
                    f"Pedido de compra '{self.name}':\n"
                    f"Deve ter pelo menos um artigo físico das áreas: {areas}"
                )

    def _prepare_supplier_info(self, partner, line, price, currency):
        """Override para gravar variante específica no supplierinfo quando template tem múltiplas variantes."""
        vals = super()._prepare_supplier_info(partner, line, price, currency)
        if line.product_id.product_tmpl_id.product_variant_count > 1:
            vals['product_id'] = line.product_id.id
        return vals

    def _add_supplier_to_product(self):
        """Override para criar supplierinfo por variante quando template tem múltiplas variantes.
        Baseado no standard Odoo 18 purchase_order.py _add_supplier_to_product.
        """
        for line in self.order_line:
            partner = self.partner_id if not self.partner_id.parent_id else self.partner_id.parent_id
            if not line.product_id:
                continue

            price = line.price_unit
            if line.product_id.product_tmpl_id.uom_po_id != line.product_uom:
                default_uom = line.product_id.product_tmpl_id.uom_po_id
                price = line.product_uom._compute_price(price, default_uom)

            if line.product_id.product_tmpl_id.product_variant_count > 1:
                # Múltiplas variantes: verificar se já existe supplierinfo para esta VARIANTE + parceiro
                existing = line.product_id.product_tmpl_id.seller_ids.filtered(
                    lambda s: s.partner_id in (partner | self.partner_id) and s.product_id == line.product_id
                )
                if existing:
                    # Actualizar preço se diferente
                    existing[0].sudo().write({'price': price, 'currency_id': line.currency_id.id})
                    continue
            else:
                # Standard: verificar por template
                already_seller = (partner | self.partner_id) & line.product_id.seller_ids.mapped('partner_id')
                if already_seller:
                    # Actualizar preço do seller existente
                    seller_existing = line.product_id.seller_ids.filtered(
                        lambda s: s.partner_id in (partner | self.partner_id)
                    )
                    if seller_existing:
                        seller_existing[0].sudo().write({'price': price, 'currency_id': line.currency_id.id})
                    continue

            if len(line.product_id.seller_ids) > 10:
                continue

            supplierinfo = self._prepare_supplier_info(partner, line, price, line.currency_id)
            seller = line.product_id._select_seller(
                partner_id=line.partner_id,
                quantity=line.product_qty,
                date=line.order_id.date_order and line.order_id.date_order.date(),
                uom_id=line.product_uom)
            if seller:
                supplierinfo['product_name'] = seller.product_name
                supplierinfo['product_code'] = seller.product_code
            vals = {
                'seller_ids': [(0, 0, supplierinfo)],
            }
            line.product_id.product_tmpl_id.sudo().write(vals)

    def button_confirm_final(self):
        """Compatibilidade temporária com chamadas do antigo wizard."""
        return self.button_confirm()

    def _create_picking(self):
        """Override para sugerir localização de consumo interno quando todos os produtos são fixed_asset."""
        res = super()._create_picking()
        for order in self:
            for picking in order.picking_ids.filtered(lambda p: p.state == 'assigned' and p.picking_type_code == 'incoming'):
                if not picking.move_ids:
                    continue
                all_fixed = all(
                    m.product_id.product_classification == 'fixed_asset'
                    for m in picking.move_ids
                    if m.product_id
                )
                if all_fixed:
                    consumption_loc = self.env['stock.location'].search([
                        ('usage', '=', 'internal'),
                        ('is_consumption', '=', True),
                        ('company_id', '=', picking.company_id.id),
                    ], limit=1)
                    if consumption_loc:
                        picking.location_dest_id = consumption_loc
        return res
    
    def button_cancel(self):
        """Override para bloquear cancelamento com picking validado ou fatura.
        Apenas Purchase Admin (group_purchase_manager) pode cancelar."""
        if not self.env.user.has_group('purchase.group_purchase_manager'):
            raise AccessError(_("Apenas administradores de compras podem cancelar cotações/pedidos de compra."))
        for order in self:
            # Verificar se tem import document finalizado
            import_doc = self.env['import.document'].search([
                ('purchase_order_ids', 'in', order.id),
                ('state', '=', 'done'),
            ], limit=1)
            if import_doc:
                raise ValidationError(
                    f"Não é possível cancelar o pedido de compra '{order.name}'.\n\n"
                    f"Está associado ao Documento de Importação '{import_doc.name}' que já está finalizado.\n\n"
                    f"Não é permitido cancelar pedidos com importação concluída."
                )

            # Verificar se tem picking validado
            validated_pickings = order.picking_ids.filtered(lambda p: p.state == 'done')
            if validated_pickings:
                picking_names = ', '.join(validated_pickings.mapped('name'))
                raise ValidationError(
                    f"Não é possível cancelar o pedido de compra '{order.name}'.\n\n"
                    f"Existem receções já validadas:\n{picking_names}\n\n"
                    f"Não é permitido cancelar pedidos com receções concluídas."
                )

            # Verificar se tem fatura (exceto canceladas)
            active_invoices = order.invoice_ids.filtered(lambda i: i.state != 'cancel')
            if active_invoices:
                invoice_names = ', '.join(active_invoices.mapped('name'))
                raise ValidationError(
                    f"Não é possível cancelar o pedido de compra '{order.name}'.\n\n"
                    f"Existem faturas de fornecedor associadas:\n{invoice_names}\n\n"
                    f"Não é permitido cancelar pedidos com faturas."
                )

        return super(PurchaseOrder, self).button_cancel()

    def button_draft(self):
        """Bloquear reset para rascunho se import document finalizado."""
        for order in self:
            import_doc = self.env['import.document'].search([
                ('purchase_order_ids', 'in', order.id),
                ('state', '=', 'done'),
            ], limit=1)
            if import_doc:
                raise ValidationError(
                    f"Não é possível retornar para rascunho o pedido '{order.name}'.\n\n"
                    f"Está associado ao Documento de Importação '{import_doc.name}' que já está finalizado."
                )
        return super(PurchaseOrder, self).button_draft()
