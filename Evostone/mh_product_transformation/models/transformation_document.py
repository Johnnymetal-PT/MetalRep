from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round
from datetime import datetime
from markupsafe import Markup

class TransformationDocument(models.Model):
    _name = 'transformation.document'
    _description = 'Documento de Transformação'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'transformation.document.pcmp']
    _order = 'date_document desc, name desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Número do Documento',
        required=True,
        readonly=True,
        copy=False,
        default=lambda self: 'Novo',
        tracking=True
    )

    date_document = fields.Date(
        string='Data do Documento',
        required=True,
        default=fields.Date.context_today,
        tracking=True
    )

    date_transit = fields.Datetime(
        string='Data de Envio em Trânsito',
        tracking=True,
        readonly=True,
        help='Data em que os produtos foram enviados em trânsito'
    )

    date_transforming = fields.Datetime(
        string='Data Envio para Transformação',
        tracking=True,
        readonly=True,
        help='Data em que os produtos foram enviados para o transformador'
    )

    date_reception = fields.Datetime(
        string='Data de Receção',
        tracking=True,
        readonly=True,
        help='Data em que os produtos transformados foram recebidos'
    )

    date_done = fields.Datetime(
        string='Data de Conclusão',
        tracking=True,
        readonly=True,
        help='Data em que a transformação foi concluída e validada'
    )

    # Logistics Tracking
    carrier_id = fields.Many2one(
        'res.partner',
        string='Transportador',
        tracking=True,
        domain="[('is_carrier', '=', True), ('supplier_rank', '>', 0)]",
        help='Transportador responsável pela logística da transformação'
    )

    date_expected_departure = fields.Date(
        string='Data Prevista de Saída',
        tracking=True,
        help='Data prevista para saída dos produtos da localização de origem'
    )

    date_expected_arrival = fields.Date(
        string='Data Prevista de Entrada',
        tracking=True,
        help='Data prevista para chegada dos produtos transformados'
    )

    daily_cost = fields.Monetary(
        string='Custo por Dia',
        currency_field='currency_id',
        tracking=True,
        help='Custo diário de armazenamento/espera durante a transformação'
    )

    days_stopped = fields.Integer(
        string='Dias Parado',
        compute='_compute_logistics_tracking',
        help='Dias desde a saída (date_transit) até hoje (em curso) ou até à conclusão'
    )

    total_waiting_cost = fields.Monetary(
        string='Custo Total de Espera',
        compute='_compute_logistics_tracking',
        currency_field='currency_id',
        help='Custo total calculado (dias_parado × custo_por_dia) — KPI, não entra no custo dos produtos'
    )

    logistics_status = fields.Selection([
        ('on_time', 'No Prazo'),
        ('delayed', 'Atrasado'),
        ('waiting', 'Em Espera')
    ], string='Status Logístico', compute='_compute_logistics_tracking')

    transformer_id = fields.Many2one(
        'res.partner',
        string='Transformador',
        required=True,
        tracking=True,
        domain="[('is_transformer', '=', True), ('supplier_rank', '>', 0)]",
        help='Parceiro transformador que realizará a transformação dos produtos'
    )

    location_origin_id = fields.Many2one(
        'stock.location',
        string='Localização de Origem',
        required=True,
        domain="[('usage', '=', 'internal')]",
        help='Localização de onde sairão os produtos para transformação',
        tracking=True
    )

    location_dest_id = fields.Many2one(
        'stock.location',
        string='Localização de Destino',
        required=True,
        domain="[('usage', '=', 'internal')]",
        help='Localização onde serão recebidos os produtos transformados',
        tracking=True
    )

    location_production_id = fields.Many2one(
        'stock.location',
        string='Localização de Produção',
        readonly=True,
        help='Localização de produção (transformação), tipo "production" como no '
             'MRP: o input é consumido PARA esta localização (SVL out, ao PCMP) e '
             'o output é produzido A PARTIR dela (SVL in). Preenchida no '
             'action_start por _get_or_create_transformation_locations.'
    )

    state = fields.Selection([
        ('draft', 'Pendente'),
        ('transit', 'Em Trânsito'),
        ('transforming', 'Em Transformação'),
        ('reception', 'Em Receção'),
        ('done', 'Concluído'),
        ('cancel', 'Cancelado')
    ], string='Estado', default='draft', required=True, tracking=True, copy=False)

    input_line_ids = fields.One2many(
        'transformation.line.input',
        'transformation_id',
        string='Produtos para Transformar'
    )

    output_line_ids = fields.One2many(
        'transformation.line.output',
        'transformation_id',
        string='Produtos Finais'
    )

    has_unapproved_differences = fields.Boolean(
        string='Tem Diferenças Não Aprovadas',
        compute='_compute_has_unapproved_differences',
        store=False,
        help='Indica se existem linhas com ganho/perda pendentes de aprovação'
    )

    total_value = fields.Float(
        string='Valor Total da Mercadoria',
        compute='_compute_total_value',
        store=True,
        help='Valor total dos produtos a serem transformados'
    )

    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        required=True,
        readonly=True,
        default=lambda self: self.env.company
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id',
        store=True,
        readonly=True
    )

    notes = fields.Text(string='Observações')

    # Relação com Pickings
    picking_ids = fields.One2many(
        'stock.picking',
        'transformation_id',
        string='Movimentos de Stock',
        help='Todos os pickings gerados por este documento de transformação'
    )

    picking_count = fields.Integer(
        string='Nº de Movimentos',
        compute='_compute_picking_count'
    )

    # Ordens de Compra de Serviços
    service_purchase_order_ids = fields.Many2many(
        'purchase.order',
        'transformation_service_purchase_rel',
        'transformation_id',
        'purchase_order_id',
        string='Ordens de Compra de Serviços',
        help="PO's de serviços disponíveis (não associadas a importações) que serão distribuídas como landed cost nos produtos finais"
    )

    available_po_ids = fields.Many2many(
        'purchase.order',
        compute='_compute_available_po_ids',
        string='POs Disponíveis',
        help='Purchase Orders disponíveis para seleção (não vinculadas a importações)'
    )

    total_service_cost = fields.Float(
        string='Custo Total de Serviços',
        compute='_compute_service_costs',
        store=True,
        compute_sudo=True,
        digits='Product Price',
        help="Soma de todas as PO's de serviço vinculadas"
    )

    service_cost_distributed = fields.Boolean(
        string='Custos Distribuídos',
        compute='_compute_service_costs',
        store=True,
        compute_sudo=True,
        help='Indica se os custos de serviço foram distribuídos nos outputs'
    )

    @api.depends('input_line_ids.subtotal')
    def _compute_total_value(self):
        for record in self:
            record.total_value = sum(line.subtotal for line in record.input_line_ids)

    @api.depends('input_line_ids.has_difference', 'input_line_ids.admin_approved')
    def _compute_has_unapproved_differences(self):
        """Verificar se há diferenças pendentes de aprovação"""
        for record in self:
            record.has_unapproved_differences = any(
                line.has_difference and not line.admin_approved
                for line in record.input_line_ids
            )

    @api.depends('service_purchase_order_ids', 'service_purchase_order_ids.amount_total', 'output_line_ids.landed_cost')
    def _compute_service_costs(self):
        """Calcular custo total de serviços"""
        for record in self:
            record.total_service_cost = sum(
                po.amount_total for po in record.service_purchase_order_ids
            )
            # Verificar se custos foram distribuídos
            record.service_cost_distributed = (
                record.total_service_cost > 0 and
                any(line.landed_cost > 0 for line in record.output_line_ids)
            )

    @api.depends('date_transit', 'date_done', 'date_expected_arrival', 'daily_cost', 'state')
    def _compute_logistics_tracking(self):
        """KPI logístico: dias parados e custo de espera.

        - **Cumulativo**: mede sempre desde a saída real (``date_transit``) até
          hoje (em curso) ou até ``date_done`` (concluído) — não reinicia por fase.
        - **Prazo único**: o atraso é medido contra a data prevista de entrada
          (``date_expected_arrival``), que é o compromisso de retorno dos
          transformados.
        - Campos **não-stored** (live) — o cálculo depende de ``today``, logo tem
          de recalcular a cada leitura para reflectir os dias reais.
        - Apenas KPI: ``total_waiting_cost`` **não** entra no custo dos produtos.
        """
        today = fields.Date.today()

        def _as_date(value):
            return value.date() if isinstance(value, datetime) else value

        for record in self:
            days_stopped = 0
            total_waiting_cost = 0.0
            logistics_status = 'on_time'

            arrival = record.date_expected_arrival
            transit = _as_date(record.date_transit)

            if record.state in ('transit', 'transforming', 'reception'):
                if transit:
                    days_stopped = (today - transit).days
                logistics_status = 'delayed' if (arrival and today > arrival) else 'waiting'

            elif record.state == 'done':
                done = _as_date(record.date_done)
                if transit and done:
                    days_stopped = (done - transit).days
                if arrival and done:
                    logistics_status = 'on_time' if done <= arrival else 'delayed'

            if days_stopped < 0:
                days_stopped = 0
            if days_stopped > 0 and record.daily_cost > 0:
                total_waiting_cost = days_stopped * record.daily_cost

            record.days_stopped = days_stopped
            record.total_waiting_cost = total_waiting_cost
            record.logistics_status = logistics_status

    @api.depends('picking_ids')
    def _compute_picking_count(self):
        for record in self:
            record.picking_count = len(record.picking_ids)

    def action_view_pickings(self):
        """Abrir lista de pickings relacionados"""
        self.ensure_one()
        return {
            'name': 'Movimentos de Stock',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('transformation_id', '=', self.id)],
            'context': {'default_transformation_id': self.id},
        }

    def action_open_stock_wizard(self):
        """Abrir wizard de seleção de estoque disponível para transformação

        Este método é chamado por transformation.line.input.action_open_stock_wizard()
        """
        self.ensure_one()

        # Criar wizard
        wizard = self.env['transformation.stock.wizard'].create({
            'transformation_id': self.id,
        })

        # Computar estoque disponível
        wizard._compute_available_stock()

        # Retornar action para abrir as linhas do wizard
        return {
            'name': 'Selecionar Estoque para Transformação',
            'type': 'ir.actions.act_window',
            'res_model': 'transformation.stock.wizard.line',
            'view_mode': 'list,form',
            'views': [
                (self.env.ref('mh_product_transformation.view_transformation_stock_wizard_line_list').id, 'list'),
                (self.env.ref('mh_product_transformation.view_transformation_stock_wizard_line_form').id, 'form'),
            ],
            'search_view_id': self.env.ref('mh_product_transformation.view_transformation_stock_wizard_line_search').id,
            'domain': [('wizard_id', '=', wizard.id)],
            'context': {
                'search_default_available': 1,
                'search_default_group_product': 1,
            },
            'target': 'new',
        }

    def _transformation_parent_location(self):
        """Localização-pai (view) da empresa onde pendurar as de trânsito."""
        self.ensure_one()
        Location = self.env['stock.location']
        return Location.search([
            ('usage', '=', 'view'),
            ('name', 'in', ['Partners']),
            ('company_id', '=', self.company_id.id),
        ], limit=1) or Location.search([
            ('usage', '=', 'view'),
            ('company_id', '=', self.company_id.id),
        ], limit=1)

    def _get_or_create_transformation_locations(self):
        """Garante a localização de PRODUÇÃO (transformação) da EMPRESA.

        Chamado no action_start — NÃO é um compute (não se devem criar
        registos dentro de um compute). Usa uma localização do tipo
        'production' (como o MRP): o input é consumido PARA esta localização
        (SVL out, ao PCMP) e o output é produzido A PARTIR dela (SVL in).
        Procura/cria sempre com company_id (isolamento multi-empresa).
        """
        Location = self.env['stock.location']
        for record in self:
            company = record.company_id
            if (record.location_production_id
                    and record.location_production_id.company_id == company):
                continue
            location = Location.search([
                ('name', '=', 'Transformação - Produção'),
                ('usage', '=', 'production'),
                ('company_id', '=', company.id),
            ], limit=1)
            if not location:
                parent = record._transformation_parent_location()
                location = Location.create({
                    'name': 'Transformação - Produção',
                    'usage': 'production',
                    'location_id': parent.id if parent else False,
                    'company_id': company.id,
                })
            record.location_production_id = location.id

    def _distribute_service_costs(self):
        """Distribuir custos de serviço proporcionalmente pelos outputs"""
        self.ensure_one()

        # SEMPRE verificar se devemos resetar landed_cost para 0
        # Se não há PO's de serviço ou custo é 0, resetar todos os landed_cost
        if not self.service_purchase_order_ids or self.total_service_cost <= 0:
            # Resetar todos os landed_cost para 0.0
            for line in self.output_line_ids:
                line.landed_cost = 0.0
            return

        if not self.output_line_ids:
            return

        # Volume total consumido por todos os outputs
        total_volume_consumed = sum(line.volume_consumed for line in self.output_line_ids)

        if total_volume_consumed <= 0:
            # Resetar todos os landed_cost para 0.0 se não há volume consumido
            for line in self.output_line_ids:
                line.landed_cost = 0.0
            return

        # Obter precisão da moeda
        precision_digits = self.currency_id.decimal_places if self.currency_id else 2

        # Distribuir com arredondamento correcto
        total_distributed = 0.0
        lines_with_volume = [l for l in self.output_line_ids if l.volume_consumed > 0 and l.quantity > 0]

        for i, line in enumerate(lines_with_volume):
            proportion = line.volume_consumed / total_volume_consumed

            if i == len(lines_with_volume) - 1:
                # Última linha recebe o resto para garantir total correcto
                line.landed_cost = float_round(
                    self.total_service_cost - total_distributed,
                    precision_digits=precision_digits
                )
            else:
                allocated = float_round(
                    self.total_service_cost * proportion,
                    precision_digits=precision_digits
                )
                line.landed_cost = allocated
                total_distributed += allocated

        # Linhas sem volume recebem zero
        for line in self.output_line_ids:
            if line.volume_consumed <= 0 or line.quantity <= 0:
                line.landed_cost = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Novo') == 'Novo':
                # Manter como DRAFT enquanto está pendente
                vals['name'] = 'DRAFT'
        return super().create(vals_list)

    def write(self, vals):
        """Override write para distribuir custos automaticamente"""
        result = super().write(vals)

        # Se mudou PO's de serviço, redistribuir custos
        if 'service_purchase_order_ids' in vals:
            for record in self:
                if record.state == 'draft':
                    record._distribute_service_costs()

        return result

    def action_approve_all_differences(self):
        """Aprovar todas as diferenças (ganhos/perdas) de uma vez"""
        self.ensure_one()

        # Verificar se usuário é admin
        if not self.env.user.has_group('base.group_system'):
            raise UserError('Apenas administradores podem aprovar diferenças.')

        # Buscar todas as linhas de input com diferença não aprovada
        lines_to_approve = self.input_line_ids.filtered(
            lambda l: l.has_difference and not l.admin_approved
        )

        if not lines_to_approve:
            raise UserError('Não há diferenças pendentes de aprovação.')

        # Contar ganhos e perdas
        gains = lines_to_approve.filtered('is_gain')
        losses = lines_to_approve.filtered('is_loss')

        # Aprovar todas
        lines_to_approve.write({'admin_approved': True})

        # Registar no chatter quem aprovou (auditoria)
        self._post_approval_message(lines_to_approve)

        # Precisão dinâmica (casas decimais configuradas para quantidades)
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # Retornar notificação
        message = []
        if gains:
            total_gain = sum(gains.mapped('volume_difference'))
            message.append(f'📈 {len(gains)} ganho(s): +{total_gain:.{precision}f}')
        if losses:
            total_loss = sum(losses.mapped('volume_difference'))
            message.append(f'📉 {len(losses)} perda(s): {total_loss:.{precision}f}')

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Diferenças Aprovadas',
                'message': f"✅ {len(lines_to_approve)} linha(s) aprovada(s):\n" + '\n'.join(message),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def _post_approval_message(self, lines):
        """Regista no chatter quem aprovou as diferenças (ganho/perda) e o
        resumo. O autor e a data ficam automaticamente no message_post."""
        self.ensure_one()
        if not lines:
            return
        # Precisão dinâmica (casas decimais configuradas para quantidades)
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        gains = lines.filtered('is_gain')
        losses = lines.filtered('is_loss')
        parts = []
        if gains:
            parts.append(f"📈 {len(gains)} ganho(s): +{sum(gains.mapped('volume_difference')):.{precision}f}")
        if losses:
            parts.append(f"📉 {len(losses)} perda(s): {sum(losses.mapped('volume_difference')):.{precision}f}")
        detail = "<br/>".join(
            f"• {l.product_id.display_name} "
            f"({l.lot_id.name if l.lot_id else 'sem lote'}): "
            f"{l.volume_difference:+.{precision}f}"
            for l in lines
        )
        self.message_post(
            body=Markup(
                "✅ <b>Diferenças aprovadas</b> por <b>%s</b><br/>%s<br/><br/>%s"
            ) % (self.env.user.name, "<br/>".join(parts), detail),
            subject='Aprovação de Diferenças',
            message_type='notification',
            subtype_xmlid='mail.mt_note'
        )

    def action_start(self):
        """Iniciar transformação - Criar 2 pickings em assigned (saída + entrada)"""
        self.ensure_one()

        if not self.input_line_ids:
            raise UserError('Adicione produtos para transformar.')

        # Validar que produtos com tracking por lote tenham lote selecionado
        for line in self.input_line_ids:
            if line.product_id.tracking == 'lot' and not line.lot_id:
                raise UserError(
                    f'O produto "{line.product_id.display_name}" tem rastreamento por lote. '
                    f'Selecione um lote antes de iniciar.'
                )

        # Gerar número de sequência real ao iniciar
        if self.name == 'DRAFT':
            self.name = self.env['ir.sequence'].next_by_code('transformation.document') or 'TRANSF/001'

        # Garantir localização de produção (por empresa) antes de criar o picking
        self._get_or_create_transformation_locations()

        Picking = self.env['stock.picking']
        Move = self.env['stock.move']

        # Buscar picking type de SAÍDA (delivery/outgoing)
        picking_type_out = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)

        if not picking_type_out:
            picking_type_out = self.env['stock.picking.type'].create({
                'name': 'Ordens de Entrega',
                'code': 'outgoing',
                'sequence_code': 'OUT',
                'company_id': self.company_id.id,
            })

        # ===== PICKING OUT: Origem → Produção (consumo do input ao PCMP) =====
        # NOTA: o picking de ENTRADA (placas) NÃO é criado aqui — é criado no
        # action_done, a partir dos outputs declarados na recepção.
        picking_out = Picking.create({
            'picking_type_id': picking_type_out.id,
            'location_id': self.location_origin_id.id,
            'location_dest_id': self.location_production_id.id,
            'origin': f'{self.name} - Saída para Transformação',
            'transformation_id': self.id,
        })

        for line in self.input_line_ids:
            move_vals = {
                'picking_id': picking_out.id,
                'name': f'Saída: {line.product_id.display_name}',
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'product_uom': line.product_uom_id.id,
                'location_id': self.location_origin_id.id,
                'location_dest_id': self.location_production_id.id,
                'length': line.length,
                'width': line.width,
                'thickness': line.thickness,
                'units_qty': line.units_qty,
                'transformation_id': self.id,
            }

            # Adicionar restrict_lot_id se houver lote
            if line.lot_id:
                move_vals['restrict_lot_id'] = line.lot_id.id
                move_vals['lot_name'] = line.lot_id.base_lot_name

            Move.create(move_vals)

        # Confirmar, reservar e validar picking OUT → input sai/consome ao PCMP
        picking_out.action_confirm()
        picking_out.action_assign()
        picking_out.with_context(from_transformation_document=True).button_validate()

        self.write({
            'state': 'transit',
            'date_transit': fields.Datetime.now()
        })

        # Se já houver placas declaradas, criar desde já o picking de entrada
        # (previsão de stock a chegar). Caso contrário, será criado quando se
        # adicionarem placas em qualquer estado até à recepção.
        self._sync_reception_picking()

        self.message_post(
            body=Markup(
                "📤 <b>Input Enviado para Transformação</b><br/><br/>"
                "Picking de saída validado: <b>%s</b><br/>"
                "Input consumido. As placas serão declaradas na recepção."
            ) % (picking_out.name,),
            subject='Enviado em Trânsito',
            message_type='notification',
            subtype_xmlid='mail.mt_note'
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Enviado em Trânsito'),
                'message': _("Input enviado e consumido.\nPicking de saída validado: %s\nDeclare as placas na recepção.") % (
                    picking_out.name,
                ),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def action_transforming(self):
        """Marcar como em transformação - Produtos já estão com o transformador"""
        self.ensure_one()

        # Buscar picking OUT para verificar se foi validado
        picking_out = self.picking_ids.filtered(
            lambda p: p.location_id == self.location_origin_id and
                     p.location_dest_id == self.location_production_id and
                     p.state == 'done'
        )

        if not picking_out:
            raise UserError('Picking de saída não encontrado ou não foi validado.')

        self.write({
            'state': 'transforming',
            'date_transforming': fields.Datetime.now()
        })
        self.message_post(
            body=Markup(
                "🔧 <b>Produtos em Transformação</b><br/><br/>"
                "Produtos estão agora em transformação no transformador externo"
            ),
            subject='Em Transformação',
            message_type='notification',
            subtype_xmlid='mail.mt_note'
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Em Transformação'),
                'message': _("Produtos estão agora em transformação no transformador externo."),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def action_reception(self):
        """Receber — AQUI declaram-se os produtos finais (placas).

        É a transição Em Transformação → Em Receção. Obriga a ter as linhas de
        output (o que voltou do transformador) e valida lotes + ganho/perda.
        Em receção as linhas ainda podem ser alteradas até ao action_done.
        """
        self.ensure_one()

        # Ao RECEBER é obrigatório ter as linhas de output (placas)
        if not self.output_line_ids:
            raise UserError('Adicione os produtos finais (placas) recebidos antes de receber.')

        # Validar lot_name dos outputs rastreados
        for line in self.output_line_ids:
            if line.product_id.tracking in ('lot', 'serial') and not line.lot_name:
                raise UserError(
                    f'O produto "{line.product_id.display_name}" requer rastreamento por lote. '
                    f'Informe o nome do lote para este produto.'
                )

        # Validar aprovação de ganho/perda (agora há outputs para comparar)
        for line in self.input_line_ids:
            if line.has_difference and not line.admin_approved:
                diff_type = "GANHO" if line.is_gain else "PERDA"
                diff_icon = "📈" if line.is_gain else "📉"
                uom_name = line.product_uom_id.name if line.product_uom_id else ('m³' if line.product_form == 'block' else 'm²')
                raise UserError(
                    f'{diff_icon} {diff_type} DETECTADO - Aprovação de Administrador Necessária!\n\n'
                    f'Produto: {line.product_id.display_name}\n'
                    f'Lote: {line.lot_id.name if line.lot_id else "N/A"}\n\n'
                    f'📊 Análise:\n'
                    f'  • Volume/Área Disponível: {line.quantity:.4f} {uom_name}\n'
                    f'  • Volume/Área Consumido: {line.volume_consumed:.4f} {uom_name}\n'
                    f'  • Diferença: {line.volume_difference:+.4f} {uom_name} ({line.volume_difference_percent:+.2f}%)\n\n'
                    f'{"✅ Este é um ganho positivo na transformação!" if line.is_gain else "⚠️ Haverá perda de material na transformação."}\n\n'
                    f'👮 Apenas administradores podem aprovar esta diferença.\n'
                    f'Marque o campo "Aprovado por Admin" na linha de entrada antes de receber.'
                )

        self.write({
            'state': 'reception',
            'date_reception': fields.Datetime.now()
        })
        self.message_post(
            body=Markup(
                "📥 <b>Produtos Recebidos</b><br/><br/>"
                "Produtos transformados foram recebidos<br/>"
                "Aguardando validação final no sistema"
            ),
            subject='Produtos Recebidos',
            message_type='notification',
            subtype_xmlid='mail.mt_note'
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Produtos Recebidos'),
                'message': _("Produtos transformados foram recebidos.\nAguardando validação final no sistema."),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def _reception_picking_type(self):
        """Tipo de operação de ENTRADA (incoming) da empresa, criando se faltar."""
        self.ensure_one()
        picking_type_in = self.env['stock.picking.type'].search([
            ('code', '=', 'incoming'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        if not picking_type_in:
            picking_type_in = self.env['stock.picking.type'].create({
                'name': 'Recebimentos',
                'code': 'incoming',
                'sequence_code': 'IN',
                'company_id': self.company_id.id,
            })
        return picking_type_in

    def _reception_move_vals(self, line):
        """Valores do stock.move de ENTRADA correspondente a uma output line."""
        self.ensure_one()
        vals = {
            'name': f'Entrada: {line.product_id.display_name}',
            'product_id': line.product_id.id,
            'product_uom_qty': line.quantity,
            'product_uom': line.product_uom_id.id,
            'location_id': self.location_production_id.id,
            'location_dest_id': self.location_dest_id.id,
            'length': line.length,
            'width': line.width,
            'thickness': line.thickness,
            'units_qty': line.units_qty,
            'transformation_id': self.id,
            'price_unit': line.price_unit,
        }
        if line.product_id.tracking in ('lot', 'serial'):
            vals['lot_name'] = line.lot_name
        return vals

    def _get_reception_picking(self):
        """Picking de ENTRADA (placas) ainda não validado, se existir."""
        self.ensure_one()
        return self.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'incoming'
            and p.state not in ('done', 'cancel')
        )[:1]

    def _sync_reception_picking(self):
        """Mantém o picking de ENTRADA (placas) em sincronia com as output_line_ids.

        É a FONTE da previsão de stock a chegar: um picking confirmado (não
        validado) cujos moves espelham as placas declaradas. Sincronização só
        forward (output -> move); o picking é readonly para o utilizador, logo
        não há sincronização reversa.

        - Só actua enquanto o bloco está no transformador
          (transit/transforming/reception). Em rascunho não há previsão; em
          done/cancel não se mexe.
        - Sem placas declaradas -> remove o picking (se existir e não validado).
        - Com placas -> cria/actualiza o picking e os moves linha a linha.
        """
        self.ensure_one()
        if self.state not in ('transit', 'transforming', 'reception'):
            return

        picking_in = self._get_reception_picking()
        outputs = self.output_line_ids

        # Sem placas -> não há previsão; limpar o picking se existir
        if not outputs:
            if picking_in:
                picking_in.move_ids.filtered(
                    lambda m: m.state not in ('done', 'cancel')
                ).unlink()
                picking_in.unlink()
            return

        # Garantir localização de produção antes de criar moves
        self._get_or_create_transformation_locations()

        Move = self.env['stock.move']
        # Cabeçalho do picking, se ainda não existe
        if not picking_in:
            picking_in = self.env['stock.picking'].create({
                'picking_type_id': self._reception_picking_type().id,
                'location_id': self.location_production_id.id,
                'location_dest_id': self.location_dest_id.id,
                'origin': f'{self.name} - Entrada de Transformados',
                'transformation_id': self.id,
            })

        # Sincronizar moves <-> output lines
        kept_moves = Move
        for line in outputs:
            move = line.stock_move_id if line.stock_move_id in picking_in.move_ids else False
            vals = self._reception_move_vals(line)
            if move and move.state not in ('done', 'cancel'):
                move.write(vals)
            else:
                vals['picking_id'] = picking_in.id
                move = Move.create(vals)
                # Ligação forward output -> move (stock_move_id não dispara sync)
                line.write({'stock_move_id': move.id})
                move.write({'transformation_output_line_id': line.id})
            kept_moves |= move

        # Remover moves de placas que foram apagadas
        orphans = picking_in.move_ids.filtered(
            lambda m: m not in kept_moves and m.state not in ('done', 'cancel')
        )
        if orphans:
            orphans.unlink()

        # Confirmar moves novos (não reservar) -> alimenta a previsão a chegar.
        # O merge é evitado pelo mh_inventory, que adiciona lot_name/length/
        # width/thickness aos _prepare_merge_moves_distinct_fields (placas com
        # lote/dimensões diferentes nunca fundem).
        draft_moves = picking_in.move_ids.filtered(lambda m: m.state == 'draft')
        if draft_moves:
            draft_moves._action_confirm()
        return picking_in

    def action_done(self):
        """Validar entrada com PCMP e Landed Costs

        Fluxo seguindo padrão mh_purchase:
        1. Buscar picking IN
        2. Actualizar custos BASE dos moves (SEM landed cost)
        3. Marcar moves com transformation_id
        4. Validar picking (mh_stock_valuation cria SVL e calcula PCMP)
        5. Se há service_purchase_order_ids, criar e validar landed cost
        6. O mh_stock_valuation._update_pcmp_prices() ajusta PCMP com custos adicionais
        """
        self.ensure_one()

        if not self.output_line_ids:
            raise UserError(_('Não há produtos finais (placas) para validar.'))

        # 1. Garantir que o picking de ENTRADA reflecte as placas finais
        #    (já existe desde que se declararam outputs — aqui só sincroniza)
        self._sync_reception_picking()
        picking_in = self._get_reception_picking()
        if not picking_in:
            raise UserError(_('Não foi possível preparar o picking de entrada das placas.'))

        # 2. Actualizar custos BASE dos moves (sem landed cost)
        # O landed cost será aplicado depois via stock.landed.cost
        self._update_move_base_costs(picking_in)

        # 3. Marcar moves com transformation_id (para contexto)
        for move in picking_in.move_ids:
            move.write({'transformation_id': self.id})

        # 4. Validar picking COM contexto from_transformation_document=True
        # O mh_stock_valuation cria SVL e calcula PCMP automaticamente
        picking_in.with_context(from_transformation_document=True).button_validate()

        # 5. Se há POs de serviço, criar e validar landed cost
        if self.service_purchase_order_ids:
            landed_cost = self._create_transformation_landed_cost()
            if landed_cost:
                landed_cost.compute_landed_cost()
                landed_cost.button_validate()
                # Actualizar pcmp_calculated nas output lines para auditoria
                self._update_output_lines_pcmp()

        self.write({
            'state': 'done',
            'date_done': fields.Datetime.now()
        })

        # Mensagem de conclusão
        msg_parts = [
            f"Picking <b>{picking_in.name}</b> validado",
            "Produtos em stock e PCMP atualizado"
        ]
        if self.landed_cost_id:
            msg_parts.append(f"Landed Cost <b>{self.landed_cost_id.name}</b> aplicado")

        self.message_post(
            body=Markup(
                "✅ <b>Transformação Concluída</b><br/><br/>" +
                "<br/>".join(msg_parts)
            ),
            subject='Transformação Concluída',
            message_type='notification',
            subtype_xmlid='mail.mt_note'
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Transformação Concluída'),
                'message': _("Transformação concluída!\n%s") % "\n".join([
                    p.replace('<b>', '').replace('</b>', '') for p in msg_parts
                ]),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def _update_move_base_costs(self, picking_in):
        """Actualizar price_unit dos moves com custo BASE (sem landed cost)

        Diferente do antigo _update_move_costs_from_output_lines():
        - Usa price_unit da output_line (custo proporcional do input)
        - NÃO inclui landed_cost (será aplicado via stock.landed.cost)
        - Define lot_name para criação de lot_group pelo mh_stock_valuation

        Args:
            picking_in: stock.picking de entrada a processar
        """
        self.ensure_one()

        for move in picking_in.move_ids:
            output_line = move.transformation_output_line_id
            if output_line and output_line.price_unit > 0:
                vals = {
                    'price_unit': output_line.price_unit,  # Custo BASE
                }
                # Adicionar lot_name para criação de lot_group
                if output_line.lot_name:
                    vals['lot_name'] = output_line.lot_name

                move.write(vals)

    def action_cancel(self):
        """Cancelar a transformação"""
        self.ensure_one()

        if self.state == 'done':
            raise UserError('Não é possível cancelar uma transformação concluída.')

        # Cancelar pickings que ainda não foram validados
        pickings_to_cancel = self.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel'))
        if pickings_to_cancel:
            pickings_to_cancel.action_cancel()

        self.write({'state': 'cancel'})
        self.message_post(
            body=Markup(
                "❌ <b>Transformação Cancelada</b><br/><br/>"
                "A transformação foi cancelada<br/>"
                "Pickings relacionados foram cancelados"
            ),
            subject='Transformação Cancelada',
            message_type='notification',
            subtype_xmlid='mail.mt_note'
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Transformação Cancelada'),
                'message': _("A transformação foi cancelada.\nPickings relacionados foram cancelados."),
                'type': 'warning',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def action_reset_draft(self):
        """Voltar ao estado rascunho"""
        if self.state not in ('cancel',):
            raise UserError('Apenas documentos cancelados podem voltar a rascunho.')
        self.write({'state': 'draft'})
        self.message_post(
            body=Markup(
                "🔄 <b>Documento Retornado ao Rascunho</b><br/><br/>"
                "O documento foi retornado ao estado rascunho"
            ),
            subject='Retornado ao Rascunho',
            message_type='notification',
            subtype_xmlid='mail.mt_note'
        )

    @api.depends('service_purchase_order_ids')
    def _compute_available_po_ids(self):
        """Computar POs disponíveis - excluindo vinculadas a importações"""
        PurchaseOrder = self.env['purchase.order']

        for record in self:
            # Domain base
            domain = [
                ('is_product_type', '=', False),
                ('state', 'in', ['purchase', 'done'])
            ]

            # Verificar se campo import_document_ids existe (sem criar dependência!)
            if 'import_document_ids' in PurchaseOrder._fields:
                domain.append(('import_document_ids', '=', False))

            # Buscar POs disponíveis
            available_pos = PurchaseOrder.search(domain)

            # Filtrar transformações (permitir próprio doc)
            if 'transformation_document_ids' in PurchaseOrder._fields:
                available_pos = available_pos.filtered(
                    lambda po: not po.transformation_document_ids or
                              (len(po.transformation_document_ids) == 1 and
                               record in po.transformation_document_ids)
                )

            record.available_po_ids = available_pos

    @api.constrains('service_purchase_order_ids')
    def _check_po_exclusivity(self):
        """Validar que PO não está em outro documento de importação ou transformação"""
        for doc in self:
            for po in doc.service_purchase_order_ids:
                # Verificar se PO está em documento de importação
                if hasattr(po, 'import_document_ids') and po.import_document_ids:
                    import_doc = po.import_document_ids[0]
                    raise ValidationError(
                        f"❌ Pedido de Compra {po.name} já está associado a um Documento de Importação!\n\n"
                        f"Documento: {import_doc.name}\n"
                        f"Estado: {import_doc.state}\n\n"
                        f"Cada PO só pode estar em um documento (importação OU transformação)."
                    )

                # Verificar se PO está em outro documento de transformação
                other_transformations = self.search([
                    ('id', '!=', doc.id if doc.id else 0),
                    ('service_purchase_order_ids', 'in', po.id)
                ])
                if other_transformations:
                    raise ValidationError(
                        f"❌ Pedido de Compra {po.name} já está associado a outro Documento de Transformação!\n\n"
                        f"Documento: {other_transformations[0].name}\n"
                        f"Estado: {other_transformations[0].state}\n\n"
                        f"Cada PO só pode estar em um documento de transformação."
                    )

    @api.constrains('date_expected_departure', 'date_expected_arrival', 'date_document', 'daily_cost')
    def _check_logistics_dates(self):
        """Validar datas e custos logísticos"""
        for record in self:
            # Expected departure should be >= document date
            if record.date_expected_departure and record.date_document:
                if record.date_expected_departure < record.date_document:
                    raise ValidationError(
                        f'❌ Data prevista de saída não pode ser anterior à data do documento!\n\n'
                        f'Data documento: {record.date_document}\n'
                        f'Data prevista saída: {record.date_expected_departure}'
                    )

            # Expected arrival should be >= expected departure
            if record.date_expected_arrival and record.date_expected_departure:
                if record.date_expected_arrival < record.date_expected_departure:
                    raise ValidationError(
                        f'❌ Data prevista de entrada não pode ser anterior à data prevista de saída!\n\n'
                        f'Data prevista saída: {record.date_expected_departure}\n'
                        f'Data prevista entrada: {record.date_expected_arrival}'
                    )

            # Daily cost should be non-negative
            if record.daily_cost < 0:
                raise ValidationError(
                    f'❌ Custo por dia não pode ser negativo!\n\n'
                    f'Custo informado: {record.daily_cost}'
                )
