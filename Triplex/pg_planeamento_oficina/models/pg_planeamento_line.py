# -*- coding: utf-8 -*-
"""Modelo central do painel de planeamento da oficina (uma linha por linha de venda).

Quase todos os campos são calculados a partir da venda, das ordens de fabrico ligadas e
dos movimentos de componentes. Ver o __manifest__.py para o guia completo de utilização.
"""
import base64
import io
import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError

try:
    import xlsxwriter
except ImportError:  # pragma: no cover
    xlsxwriter = None

try:
    from PIL import Image as PILImage
except ImportError:  # pragma: no cover
    PILImage = None


COMPONENT_TYPES = ('tecido', 'casco', 'inox', 'polidor', 'embalagem')

# stock.move state -> componente status (RECEBIDO / FALTA / N/A)
# done                         -> recebido
# cancel                       -> recebido (não bloqueia, ignorado)
# qualquer outro estado ativo  -> falta
# sem move                     -> na

COMPONENT_STATUS = [
    ('recebido', 'Recebido'),
    ('falta', 'Falta'),
    ('na', 'N/A'),
]

ENCOMENDA_STATUS = [
    ('rascunho', 'Rascunho'),
    ('confirmada', 'Confirmada'),
    ('producao', 'Em Produção'),
    ('concluida', 'Concluída'),
    ('cancelada', 'Cancelada'),
]

PRIORIDADE = [
    ('alta', 'Alta'),
    ('normal', 'Normal'),
    ('baixa', 'Baixa'),
    ('na', 'N/A'),
]

CORTE_STATUS = [
    ('pending', 'Pendente'),
    ('ready', 'Pronto'),
    ('progress', 'Em Curso'),
    ('done', 'Concluído'),
    ('cancel', 'Cancelado'),
]


class PgPlaneamentoLine(models.Model):
    _name = 'pg.planeamento.line'
    _description = 'Linha de Planeamento da Oficina'
    _order = 'data desc, id desc'
    _rec_name = 'enc'

    # ----- Identidade -----
    sale_line_id = fields.Many2one(
        'sale.order.line', string='Linha de Encomenda',
        required=True, ondelete='cascade', index=True,
    )
    company_id = fields.Many2one(
        'res.company', string='Empresa Odoo',
        related='sale_line_id.company_id', store=True, readonly=True,
    )
    currency_id = fields.Many2one(
        'res.currency', related='sale_line_id.currency_id', readonly=True,
    )

    # ----- Estado da encomenda (composto SO + MO) -----
    encomenda_status = fields.Selection(
        ENCOMENDA_STATUS, string='Estado',
        compute='_compute_encomenda_status', store=True,
    )

    # ----- Datas e prioridade -----
    prioridade = fields.Selection(
        PRIORIDADE, string='Prioridade', default='normal',
    )
    data = fields.Date(
        string='Data', compute='_compute_data', store=True,
        help="Data em que o processo iniciou: a mais antiga entre a data da "
             "encomenda e a data de início da ordem de produção.",
    )
    dt_prev = fields.Datetime(
        string='Data Prevista',
        related='sale_line_id.order_id.commitment_date',
        readonly=False, store=True,
    )
    # x_studio_semana é um campo Studio cujo tipo pode variar (Char, Date,
    # Many2one, etc.); usamos compute em vez de related para evitar TypeError
    # de tipos incompatíveis. Edição faz-se directamente na sale.order.
    # Semeada da SO (x_studio_semana) mas EDITÁVEL: a administração pode mudar a
    # semana de uma encomenda só para planeamento, sem escrever na SO (é computada,
    # não related). Mudar a semana move a encomenda para outra semana (via semana_id).
    semana = fields.Char(
        string='Semana',
        compute='_compute_semana', store=True, readonly=False,
    )
    semana_num = fields.Integer(
        string='Nº Semana',
        compute='_compute_semana_num', store=True, readonly=True,
        help="Versão numérica de Semana, usada para ordenação correta no pivot.",
    )
    # Ligação ao registo semanal (Planeamento Semanal). Find-or-create por texto da
    # semana, para permitir edição inline no formulário semanal sem escrever na origem.
    semana_id = fields.Many2one(
        'pg.planeamento.semana', string='Semana (Planeamento)',
        compute='_compute_semana_id', store=True, index=True, ondelete='set null',
    )

    # ----- Imagem e produto -----
    imagem = fields.Image(
        string='Imagem',
        related='sale_line_id.product_id.image_1920',
        readonly=True,
    )
    enc = fields.Char(
        string='Encomenda',
        related='sale_line_id.order_id.name', store=True, readonly=True,
    )
    cliente_id = fields.Many2one(
        'res.partner', string='Cliente',
        related='sale_line_id.order_id.partner_id', store=True, readonly=False,
    )
    contramarca = fields.Char(
        string='Contramarca',
        related='sale_line_id.order_id.x_studio_customer_ref',
        store=True, readonly=False,
    )
    designacao = fields.Char(
        string='Designação',
        related='sale_line_id.product_id.name', readonly=True,
    )
    variante = fields.Char(
        string='Variante', compute='_compute_variante', store=True,
    )
    qnt = fields.Float(
        string='Qnt',
        related='sale_line_id.product_uom_qty', readonly=False, store=True,
    )
    # Campos legados mantidos APENAS por compatibilidade: foram retirados das
    # vistas deste módulo, mas continuam a existir porque vistas guardadas na
    # base de dados (p. ex. personalizações Studio da pesquisa) ainda os podem
    # referenciar. Remover o campo do modelo partiria essas vistas.
    empresa = fields.Char(string='Empresa')
    zero_text = fields.Char(string='0')

    # ----- Ordens de Produção ligadas -----
    # Armazenado para ser pesquisável e propagar corretamente os campos que dele
    # dependem (estados, componentes, tempos). A frescura é garantida por triggers
    # em mrp.production (ver models/mrp_production.py), já que a ligação é por
    # correspondência de origem + produto e não por relação direta.
    mo_ids = fields.Many2many(
        'mrp.production', string='Ordens de Produção',
        compute='_compute_mo_ids', store=True,
    )

    # ----- Estado do posto CORTE -----
    corte_status = fields.Selection(
        CORTE_STATUS, string='Corte',
        compute='_compute_corte_status', store=True,
    )

    # ----- Componentes por tipo de fornecedor -----
    # Armazenados para serem pesquisáveis/filtráveis no painel.
    tecido = fields.Char(string='Tecido', compute='_compute_componentes', store=True)
    tecido_status = fields.Selection(
        COMPONENT_STATUS, string='Tecido Status',
        compute='_compute_componentes', store=True,
    )
    casco = fields.Char(string='Casco', compute='_compute_componentes', store=True)
    casco_status = fields.Selection(
        COMPONENT_STATUS, string='Casco Status',
        compute='_compute_componentes', store=True,
    )
    inox = fields.Char(string='Inox', compute='_compute_componentes', store=True)
    inox_status = fields.Selection(
        COMPONENT_STATUS, string='Inox Status',
        compute='_compute_componentes', store=True,
    )
    polidor = fields.Char(string='Polidor', compute='_compute_componentes', store=True)
    polidor_status = fields.Selection(
        COMPONENT_STATUS, string='Polidor Status',
        compute='_compute_componentes', store=True,
    )
    embalagem = fields.Char(string='Embalagem', compute='_compute_componentes', store=True)
    embalagem_status = fields.Selection(
        COMPONENT_STATUS, string='Embalagem Status',
        compute='_compute_componentes', store=True,
    )

    # ----- Fornecedores por componente (clicáveis) -----
    # Many2many porque um mesmo slot pode ter movimentos de fornecedores distintos.
    # Relação explícita por campo para evitar colisão de tabela (vários M2M para res.partner).
    tecido_fornecedor_ids = fields.Many2many(
        'res.partner', 'pg_plan_tecido_forn_rel', 'line_id', 'partner_id',
        string='Fornecedor Tecido', compute='_compute_componentes', store=True,
    )
    casco_fornecedor_ids = fields.Many2many(
        'res.partner', 'pg_plan_casco_forn_rel', 'line_id', 'partner_id',
        string='Fornecedor Casco', compute='_compute_componentes', store=True,
    )
    inox_fornecedor_ids = fields.Many2many(
        'res.partner', 'pg_plan_inox_forn_rel', 'line_id', 'partner_id',
        string='Fornecedor Inox', compute='_compute_componentes', store=True,
    )
    polidor_fornecedor_ids = fields.Many2many(
        'res.partner', 'pg_plan_polidor_forn_rel', 'line_id', 'partner_id',
        string='Fornecedor Polidor', compute='_compute_componentes', store=True,
    )
    embalagem_fornecedor_ids = fields.Many2many(
        'res.partner', 'pg_plan_embalagem_forn_rel', 'line_id', 'partner_id',
        string='Fornecedor Embalagem', compute='_compute_componentes', store=True,
    )

    # ----- Ordens de Compra por componente (clicáveis) -----
    tecido_po_ids = fields.Many2many(
        'purchase.order', 'pg_plan_tecido_po_rel', 'line_id', 'po_id',
        string='OC Tecido', compute='_compute_componentes', store=True,
    )
    casco_po_ids = fields.Many2many(
        'purchase.order', 'pg_plan_casco_po_rel', 'line_id', 'po_id',
        string='OC Casco', compute='_compute_componentes', store=True,
    )
    inox_po_ids = fields.Many2many(
        'purchase.order', 'pg_plan_inox_po_rel', 'line_id', 'po_id',
        string='OC Inox', compute='_compute_componentes', store=True,
    )
    polidor_po_ids = fields.Many2many(
        'purchase.order', 'pg_plan_polidor_po_rel', 'line_id', 'po_id',
        string='OC Polidor', compute='_compute_componentes', store=True,
    )
    embalagem_po_ids = fields.Many2many(
        'purchase.order', 'pg_plan_embalagem_po_rel', 'line_id', 'po_id',
        string='OC Embalagem', compute='_compute_componentes', store=True,
    )

    # ----- Produto (Many2one clicável no formulário) -----
    product_id = fields.Many2one(
        'product.product', string='Produto',
        related='sale_line_id.product_id', store=True, readonly=True,
    )

    # ----- Marca para o layout de impressão (cabeçalho/logótipo Studio) -----
    # O cabeçalho de impressão personalizado (Studio) escolhe o logótipo por
    # `x_studio_empresa` (campo que existe na SO/PO). Neste painel a marca é
    # sempre Oficinna22, por isso fornecemos esse valor para o layout funcionar.
    x_studio_empresa = fields.Char(
        string='Empresa (Logótipo)',
        compute='_compute_x_studio_empresa', store=True,
    )

    # ----- Ordens de Compra que abastecem a produção desta linha -----
    purchase_order_ids = fields.Many2many(
        'purchase.order', string='Ordens de Compra',
        compute='_compute_purchase_orders',
    )
    po_count = fields.Integer(
        string='Nº Ordens de Compra', compute='_compute_purchase_orders',
    )
    mo_count = fields.Integer(
        string='Nº Ordens de Produção', compute='_compute_mo_count',
    )

    # ----- Faturação e valores -----
    faturacao = fields.Selection(
        related='sale_line_id.invoice_status', string='Faturação',
        store=True, readonly=True,
    )
    orc = fields.Monetary(string='Orçamento', currency_field='currency_id')
    total = fields.Monetary(
        string='Total',
        related='sale_line_id.price_subtotal', store=True, readonly=True,
        currency_field='currency_id',
    )
    total_faturado = fields.Monetary(
        string='Faturado',
        related='sale_line_id.untaxed_amount_invoiced', store=True, readonly=True,
        currency_field='currency_id',
    )

    # ----- Tempos por centro de trabalho (horas) -----
    # Semeados a partir das operações reais, mas EDITÁVEIS para planeamento
    # administrativo. Por serem computados (não related), editar NUNCA escreve nas
    # operações/MO. O botão "Atualizar a partir do Odoo" volta a puxar os valores reais.
    tempo_corte_costura = fields.Float(
        string='Tempo Corte/Costura (h)', compute='_compute_tempos',
        store=True, readonly=False,
    )
    tempo_espuma_estofo = fields.Float(
        string='Tempo Espuma/Estofo (h)', compute='_compute_tempos',
        store=True, readonly=False,
    )
    tempo_embalagem = fields.Float(
        string='Tempo Embalagem (h)', compute='_compute_tempos',
        store=True, readonly=False,
    )

    # ----- Horas-pessoa por grupo de centros de trabalho -----
    # Os tempos acima são de relógio: "a Espuma levou 3 h", independentemente de lá terem
    # estado uma ou três pessoas. Estes campos multiplicam cada registo de tempo pelo número
    # de pessoas que o produziu (`pg_mrp_people_count`), que é o que aproxima o número do
    # custo real da peça.
    #
    # Ao contrário dos tempos, NÃO são editáveis: são medição, não planeamento. Um valor
    # escrito à mão aqui não teria significado nenhum.
    horas_pessoa_corte_costura = fields.Float(
        string='Horas-pessoa Corte/Costura', compute='_compute_horas_pessoa', store=True,
    )
    horas_pessoa_espuma_estofo = fields.Float(
        string='Horas-pessoa Espuma/Estofo', compute='_compute_horas_pessoa', store=True,
    )
    horas_pessoa_embalagem = fields.Float(
        string='Horas-pessoa Embalagem', compute='_compute_horas_pessoa', store=True,
    )
    horas_pessoa_total = fields.Float(
        string='Horas-pessoa Total', compute='_compute_horas_pessoa', store=True,
    )

    _sql_constraints = [
        ('sale_line_uniq', 'unique(sale_line_id)',
         'Já existe uma linha de planeamento para esta linha de encomenda.'),
    ]

    # ============================================================ COMPUTES

    @api.depends('sale_line_id.order_id.name', 'sale_line_id.product_id')
    def _compute_mo_ids(self):
        Mo = self.env['mrp.production']
        for rec in self:
            sol = rec.sale_line_id
            if sol and sol.order_id.name and sol.product_id:
                rec.mo_ids = Mo.search([
                    ('origin', '=', sol.order_id.name),
                    ('product_id', '=', sol.product_id.id),
                ])
            else:
                rec.mo_ids = Mo

    @api.depends('sale_line_id.state', 'mo_ids.state')
    def _compute_encomenda_status(self):
        for rec in self:
            so_state = rec.sale_line_id.state
            if so_state == 'cancel':
                rec.encomenda_status = 'cancelada'
                continue
            if so_state in ('draft', 'sent') or not so_state:
                rec.encomenda_status = 'rascunho'
                continue
            mo_states = set(rec.mo_ids.mapped('state'))
            if mo_states and mo_states.issubset({'done', 'cancel'}):
                rec.encomenda_status = 'concluida'
            elif mo_states & {'progress', 'to_close'}:
                rec.encomenda_status = 'producao'
            elif mo_states & {'confirmed', 'planned'}:
                rec.encomenda_status = 'producao'
            else:
                rec.encomenda_status = 'confirmada'

    @api.depends('sale_line_id.order_id.date_order', 'mo_ids.date_start')
    def _compute_data(self):
        for rec in self:
            candidates = []
            so_date = rec.sale_line_id.order_id.date_order
            if so_date:
                candidates.append(so_date.date() if hasattr(so_date, 'date') else so_date)
            for d in rec.mo_ids.mapped('date_start'):
                if d:
                    candidates.append(d.date() if hasattr(d, 'date') else d)
            rec.data = min(candidates) if candidates else False

    @api.depends('sale_line_id.product_id',
                 'sale_line_id.product_id.product_template_attribute_value_ids')
    def _compute_variante(self):
        for rec in self:
            product = rec.sale_line_id.product_id
            ptavs = product.product_template_attribute_value_ids if product else False
            if ptavs:
                rec.variante = ', '.join(ptavs.mapped('name'))
            elif product and product.default_code:
                rec.variante = product.default_code
            else:
                rec.variante = False

    def _pg_semana_from_source(self):
        """Texto da semana derivado da SO (x_studio_semana)."""
        self.ensure_one()
        val = self.sale_line_id.order_id.x_studio_semana if self.sale_line_id else False
        if not val:
            return False
        if hasattr(val, 'display_name'):
            return val.display_name
        if hasattr(val, 'isoformat'):
            return val.isoformat()
        return str(val)

    @api.depends('sale_line_id.order_id.x_studio_semana')
    def _compute_semana(self):
        for rec in self:
            rec.semana = rec._pg_semana_from_source()

    @api.depends('semana')
    def _compute_semana_num(self):
        # Primeiro número da string (suporta "1", "10", "26-S18", "Semana 5", etc.).
        for rec in self:
            match = re.search(r'\d+', rec.semana or '')
            rec.semana_num = int(match.group()) if match else 0

    @api.depends('mo_ids.workorder_ids.state',
                 'mo_ids.workorder_ids.workcenter_id.name')
    def _compute_corte_status(self):
        for rec in self:
            wos = rec.mo_ids.workorder_ids.filtered(
                lambda w: w.workcenter_id.name and 'CORTE' in w.workcenter_id.name.upper()
            )
            if not wos:
                rec.corte_status = False
                continue
            states = wos.mapped('state')
            if 'progress' in states:
                rec.corte_status = 'progress'
            elif states and all(s == 'done' for s in states):
                rec.corte_status = 'done'
            elif 'ready' in states:
                rec.corte_status = 'ready'
            elif states and all(s == 'cancel' for s in states):
                rec.corte_status = 'cancel'
            else:
                rec.corte_status = 'pending'

    @api.depends('mo_ids.move_raw_ids.state',
                 'mo_ids.move_raw_ids.product_id.display_name',
                 'mo_ids.move_raw_ids.x_supplier_type',
                 'mo_ids.move_raw_ids.x_vendor_id',
                 'mo_ids.move_raw_ids.move_orig_ids.purchase_line_id.order_id')
    def _compute_componentes(self):
        for rec in self:
            moves = rec.mo_ids.move_raw_ids
            for vtype in COMPONENT_TYPES:
                slot_moves = moves.filtered(lambda m: m.x_supplier_type == vtype)
                if not slot_moves:
                    rec[vtype] = False
                    rec[f'{vtype}_status'] = 'na'
                    rec[f'{vtype}_fornecedor_ids'] = [(5, 0, 0)]
                    rec[f'{vtype}_po_ids'] = [(5, 0, 0)]
                    continue
                names = ', '.join(slot_moves.mapped('product_id.display_name'))
                states = slot_moves.mapped('state')
                # FALTA wins over RECEBIDO when concatenating
                if all(s in ('done', 'cancel') for s in states):
                    status = 'recebido'
                else:
                    status = 'falta'
                rec[vtype] = names
                rec[f'{vtype}_status'] = status
                rec[f'{vtype}_fornecedor_ids'] = [(6, 0, slot_moves.mapped('x_vendor_id').ids)]
                pos = slot_moves.move_orig_ids.purchase_line_id.order_id
                rec[f'{vtype}_po_ids'] = [(6, 0, pos.ids)]

    @api.depends('mo_ids.move_raw_ids.move_orig_ids.purchase_line_id.order_id',
                 'sale_line_id.order_id.name')
    def _compute_purchase_orders(self):
        Po = self.env['purchase.order']
        for rec in self:
            # 1) Cadeia de abastecimento (MTO): POs que alimentam diretamente os
            #    componentes desta OP via movimentos de origem.
            pos = rec.mo_ids.move_raw_ids.move_orig_ids.purchase_line_id.order_id
            # 2) POs cuja origem refere a encomenda de venda (procura por nome da SO).
            so_name = rec.sale_line_id.order_id.name
            if so_name:
                pos |= Po.search([('origin', 'ilike', so_name)])
            rec.purchase_order_ids = pos
            rec.po_count = len(pos)

    @api.depends('mo_ids')
    def _compute_mo_count(self):
        for rec in self:
            rec.mo_count = len(rec.mo_ids)

    @api.depends('semana')
    def _compute_semana_id(self):
        Semana = self.env['pg.planeamento.semana'].sudo()
        cache = {}
        for rec in self:
            name = rec.semana
            if not name:
                rec.semana_id = False
                continue
            sem = cache.get(name)
            if not sem:
                sem = Semana.search([('semana', '=', name)], limit=1)
                if not sem:
                    sem = Semana.create({'semana': name})
                cache[name] = sem
            rec.semana_id = sem.id

    @api.depends('sale_line_id')
    def _compute_x_studio_empresa(self):
        # Painel Oficinna22: o logótipo de impressão é sempre o da Oficinna22.
        for rec in self:
            rec.x_studio_empresa = 'Oficinna22'

    def _pg_tempo_values(self):
        """Tempos reais (horas) por grupo de centros de trabalho, a partir das operações."""
        self.ensure_one()
        wos = self.mo_ids.workorder_ids

        def total_h(keywords):
            minutes = sum(
                wo.duration for wo in wos
                if wo.workcenter_id.name
                and any(k in wo.workcenter_id.name.upper() for k in keywords)
            )
            return minutes / 60.0

        return {
            'tempo_corte_costura': total_h(('CORTE', 'COSTURA')),
            'tempo_espuma_estofo': total_h(('ESPUMA', 'ESTOFO')),
            'tempo_embalagem': total_h(('EMBALAGEM',)),
        }

    def _pg_horas_pessoa_values(self):
        """Horas-pessoa por grupo de centros de trabalho.

        Soma `pg_person_hours` dos registos de tempo, agrupando pelos mesmos critérios de
        nome de centro que os tempos de relógio, para as duas leituras ficarem alinhadas
        lado a lado no painel.

        Vai directamente aos registos de tempo em vez de somar o campo agregado da ordem de
        trabalho: `mrp.workorder.pg_person_hours` não é armazenado, e depender dele num campo
        armazenado obrigaria a uma cadeia de recomputação mais frágil do que somar a fonte.
        """
        self.ensure_one()
        registos = self.mo_ids.workorder_ids.time_ids

        def total(keywords):
            return sum(
                registo.pg_person_hours
                for registo in registos
                if registo.workorder_id.workcenter_id.name
                and any(k in registo.workorder_id.workcenter_id.name.upper()
                        for k in keywords)
            )

        return {
            'horas_pessoa_corte_costura': total(('CORTE', 'COSTURA')),
            'horas_pessoa_espuma_estofo': total(('ESPUMA', 'ESTOFO')),
            'horas_pessoa_embalagem': total(('EMBALAGEM',)),
        }

    @api.depends('mo_ids.workorder_ids.time_ids.pg_person_hours',
                 'mo_ids.workorder_ids.workcenter_id.name')
    def _compute_horas_pessoa(self):
        for rec in self:
            vals = rec._pg_horas_pessoa_values()
            rec.horas_pessoa_corte_costura = vals['horas_pessoa_corte_costura']
            rec.horas_pessoa_espuma_estofo = vals['horas_pessoa_espuma_estofo']
            rec.horas_pessoa_embalagem = vals['horas_pessoa_embalagem']
            rec.horas_pessoa_total = sum(vals.values())

    @api.depends('mo_ids.workorder_ids.duration',
                 'mo_ids.workorder_ids.workcenter_id.name')
    def _compute_tempos(self):
        for rec in self:
            vals = rec._pg_tempo_values()
            rec.tempo_corte_costura = vals['tempo_corte_costura']
            rec.tempo_espuma_estofo = vals['tempo_espuma_estofo']
            rec.tempo_embalagem = vals['tempo_embalagem']

    def action_pg_resync_from_odoo(self):
        """Volta a puxar os valores reais do Odoo, descartando as edições manuais.

        Usado pelo botão (com confirmação) no planeamento administrativo. Re-semeia os
        tempos por centro de trabalho e a semana a partir dos valores reais do Odoo.
        """
        for rec in self:
            vals = rec._pg_tempo_values()
            vals['semana'] = rec._pg_semana_from_source()
            rec.write(vals)
        return True

    # ============================================================ HELPERS

    def name_get(self):
        return [(r.id, f"{r.enc or ''} — {r.designacao or ''}".strip(' —')) for r in self]

    def action_open_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': self.sale_line_id.order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_mos(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ordens de Produção',
            'res_model': 'mrp.production',
            'domain': [('id', 'in', self.mo_ids.ids)],
            'view_mode': 'tree,form',
            'target': 'current',
        }

    def action_open_purchase_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ordens de Compra',
            'res_model': 'purchase.order',
            'domain': [('id', 'in', self.purchase_order_ids.ids)],
            'view_mode': 'tree,form',
            'target': 'current',
        }

    # ============================================================ EXPORT XLSX

    def _sel_label(self, fname):
        """Etiqueta legível de um campo Selection (suporta selection callable)."""
        self.ensure_one()
        value = self[fname]
        if not value:
            return ''
        selection = self._fields[fname].selection
        if callable(selection):
            selection = selection(self)
        return dict(selection).get(value, value)

    def action_export_planeamento_xlsx(self):
        """Gera um ficheiro Excel do painel (registos selecionados, ou todos)."""
        if xlsxwriter is None:
            raise UserError(_("A biblioteca 'xlsxwriter' não está disponível no servidor."))
        records = self if self else self.search([])

        output = io.BytesIO()
        wb = xlsxwriter.Workbook(output, {'in_memory': True})
        ws = wb.add_worksheet('Planeamento')

        f_header = wb.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True,
            'border': 1, 'bg_color': '#1F1F1F', 'font_color': '#FFFFFF'})
        f_text = wb.add_format({'border': 1, 'valign': 'vcenter', 'text_wrap': True})
        f_center = wb.add_format({'border': 1, 'valign': 'vcenter', 'align': 'center'})
        f_money = wb.add_format({'border': 1, 'valign': 'vcenter', 'align': 'right', 'num_format': '#,##0.00'})
        f_date = wb.add_format({'border': 1, 'valign': 'vcenter', 'align': 'center', 'num_format': 'dd/mm/yyyy'})
        f_recebido = wb.add_format({'border': 1, 'valign': 'vcenter', 'align': 'center',
                                    'bg_color': '#C6EFCE', 'font_color': '#006100'})
        f_falta = wb.add_format({'border': 1, 'valign': 'vcenter', 'align': 'center',
                                 'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
        f_na = wb.add_format({'border': 1, 'valign': 'vcenter', 'align': 'center',
                              'bg_color': '#D9D9D9', 'font_color': '#666666'})
        f_info = wb.add_format({'border': 1, 'valign': 'vcenter', 'align': 'center',
                                'bg_color': '#BDD7EE', 'font_color': '#1F4E78'})
        f_alta = wb.add_format({'border': 1, 'valign': 'vcenter', 'align': 'center',
                                'bold': True, 'bg_color': '#FFC7CE', 'font_color': '#9C0006'})

        comp_status_fmt = {'recebido': f_recebido, 'falta': f_falta, 'na': f_na, False: f_na}

        headers = [
            ('ESTADO', 14), ('PRIORIDADE', 11), ('DATA', 11), ('IMAGEM', 12),
            ('ENC', 13), ('CLIENTE', 22), ('CONTRAMARCA', 16), ('DESIGNAÇÃO', 32),
            ('VARIANTE', 10), ('QNT', 7), ('CORTE', 11),
            ('TECIDO', 22), ('TEC. ST.', 11), ('CASCO', 18), ('CASCO ST.', 11),
            ('INOX', 16), ('INOX ST.', 11), ('POLIDOR', 20), ('POL. ST.', 11),
            ('EMBALAGEM', 16), ('EMB. ST.', 11),
            ('FATURAÇÃO', 13), ('DT.PREV', 12), ('ORC', 11), ('TOTAL', 11), ('SEMANA', 10),
        ]
        for col, (label, width) in enumerate(headers):
            ws.write(0, col, label, f_header)
            ws.set_column(col, col, width)
        ws.freeze_panes(1, 0)
        ws.autofilter(0, 0, max(len(records), 1), len(headers) - 1)

        row = 1
        for rec in records:
            ws.set_row(row, 48)
            enc_fmt = f_info if rec.encomenda_status in ('producao', 'concluida') else f_center
            ws.write(row, 0, rec._sel_label('encomenda_status'), enc_fmt)
            ws.write(row, 1, rec._sel_label('prioridade'),
                     f_alta if rec.prioridade == 'alta' else f_center)
            if rec.data:
                ws.write_datetime(row, 2, rec.data, f_date)
            else:
                ws.write(row, 2, '', f_center)
            # Imagem (miniatura) na coluna 3
            if rec.imagem:
                try:
                    raw = base64.b64decode(rec.imagem)
                    scale = 0.5
                    if PILImage is not None:
                        with PILImage.open(io.BytesIO(raw)) as im:
                            w, h = im.size
                        if w and h:
                            scale = min(60.0 / w, 60.0 / h)
                    ws.insert_image(row, 3, 'produto.png', {
                        'image_data': io.BytesIO(raw),
                        'x_scale': scale, 'y_scale': scale,
                        'object_position': 1, 'x_offset': 3, 'y_offset': 3,
                    })
                except Exception:
                    ws.write(row, 3, '', f_center)
            else:
                ws.write(row, 3, '', f_center)
            ws.write(row, 4, rec.enc or '', f_center)
            ws.write(row, 5, rec.cliente_id.display_name or '', f_text)
            ws.write(row, 6, rec.contramarca or '', f_text)
            ws.write(row, 7, rec.designacao or '', f_text)
            ws.write(row, 8, rec.variante or '', f_center)
            ws.write(row, 9, rec.qnt or 0, f_center)
            ws.write(row, 10, rec._sel_label('corte_status'),
                     f_recebido if rec.corte_status == 'done' else f_na)
            # Componentes (nome + estado), por par de colunas
            comp_cols = [
                ('tecido', 'tecido_status', 11, 12),
                ('casco', 'casco_status', 13, 14),
                ('inox', 'inox_status', 15, 16),
                ('polidor', 'polidor_status', 17, 18),
                ('embalagem', 'embalagem_status', 19, 20),
            ]
            for name_f, status_f, c_name, c_status in comp_cols:
                ws.write(row, c_name, rec[name_f] or '', f_text)
                ws.write(row, c_status, rec._sel_label(status_f),
                         comp_status_fmt.get(rec[status_f], f_na))
            ws.write(row, 21, rec._sel_label('faturacao'), f_center)
            if rec.dt_prev:
                ws.write_datetime(row, 22, rec.dt_prev, f_date)
            else:
                ws.write(row, 22, '', f_center)
            ws.write(row, 23, rec.orc or 0, f_money)
            ws.write(row, 24, rec.total or 0, f_money)
            ws.write(row, 25, rec.semana or '', f_center)
            row += 1

        wb.close()
        output.seek(0)
        attachment = self.env['ir.attachment'].create({
            'name': 'Planeamento.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }
