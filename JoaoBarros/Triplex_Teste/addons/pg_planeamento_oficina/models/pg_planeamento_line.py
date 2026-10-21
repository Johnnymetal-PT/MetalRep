# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models


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
    semana = fields.Char(
        string='Semana',
        compute='_compute_semana', store=True, readonly=True,
    )
    semana_num = fields.Integer(
        string='Nº Semana',
        compute='_compute_semana', store=True, readonly=True,
        help="Versão numérica de Semana, usada para ordenação correta no pivot.",
    )

    # ----- Empresa (free-text legado) -----
    empresa = fields.Char(string='Empresa')

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
    contramarca = fields.Char(string='Contramarca')
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
    zero_text = fields.Char(string='0')

    # ----- Ordens de Produção ligadas -----
    mo_ids = fields.Many2many(
        'mrp.production', string='Ordens de Produção',
        compute='_compute_mo_ids', store=False,
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

    @api.depends('sale_line_id.order_id.x_studio_semana')
    def _compute_semana(self):
        for rec in self:
            val = rec.sale_line_id.order_id.x_studio_semana if rec.sale_line_id else False
            if not val:
                rec.semana = False
                rec.semana_num = 0
                continue
            if hasattr(val, 'display_name'):
                text = val.display_name
            elif hasattr(val, 'isoformat'):
                text = val.isoformat()
            else:
                text = str(val)
            rec.semana = text
            # Extrai o primeiro número da string para ordenação numérica.
            # Suporta formatos como "1", "10", "26-S18", "Semana 5", etc.
            match = re.search(r'\d+', text)
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
                 'mo_ids.move_raw_ids.x_supplier_type')
    def _compute_componentes(self):
        for rec in self:
            moves = rec.mo_ids.move_raw_ids
            for vtype in COMPONENT_TYPES:
                slot_moves = moves.filtered(lambda m: m.x_supplier_type == vtype)
                if not slot_moves:
                    rec[vtype] = False
                    rec[f'{vtype}_status'] = 'na'
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
