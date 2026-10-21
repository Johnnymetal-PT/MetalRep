from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from markupsafe import Markup
import logging

_logger = logging.getLogger(__name__)


class ImportDocumentAdjustment(models.Model):
    """Ajuste pós-factura ligado a um Documento de Importação (IMP).

    Cenário: factura do fornecedor traz valores ACIMA da PO usada no IMP
    (linhas com produto landed_cost_ok=True sem ligação a PO). O IMP original
    fica intocável (state='done'); criamos um ADJ separado com o seu próprio
    landed cost + ajuste CMV para qty vendida.
    """
    _name = 'import.document.adjustment'
    _description = 'Ajuste Pós-Factura de Importação'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, name desc'

    name = fields.Char(
        string='Referência',
        default='ADJ/New',
        readonly=True,
        copy=False,
        tracking=True,
    )

    # ───────────────── Origem ─────────────────
    import_id = fields.Many2one(
        'import.document',
        string='Documento de Importação',
        required=True,
        readonly=True,
        ondelete='restrict',
        tracking=True,
        help='IMP que está a ser ajustado. O IMP em si não é modificado.',
    )
    source_invoice_id = fields.Many2one(
        'account.move',
        string='Factura Origem',
        required=True,
        readonly=True,
        domain="[('move_type', '=', 'in_invoice')]",
        tracking=True,
    )
    source_invoice_line_ids = fields.Many2many(
        'account.move.line',
        string='Linhas da Factura',
        readonly=True,
        help='Linhas da factura que originaram este ajuste (sem purchase_line_id).',
    )

    # ───────────────── Valor ─────────────────
    amount = fields.Monetary(
        string='Valor Total',
        currency_field='company_currency_id',
        tracking=True,
        help='Total do ajuste em moeda da empresa (soma dos balances das '
             'linhas-origem, já ao câmbio da factura).',
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='import_id.currency_id',
        store=True,
        readonly=True,
        help='Moeda do documento de importação (informativa).',
    )
    company_currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        string='Moeda da Empresa',
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        'res.company',
        related='import_id.company_id',
        store=True,
        readonly=True,
    )

    # ───────────────── Aplicação ─────────────────
    landed_cost_id = fields.Many2one(
        'stock.landed.cost',
        string='Landed Cost (criado)',
        readonly=True,
        copy=False,
        help='2º Landed Cost criado por este ajuste, vinculado aos pickings do IMP.',
    )
    cmv_adjustment_move_id = fields.Many2one(
        'account.move',
        string='Ajuste CMV',
        readonly=True,
        copy=False,
        help='Lançamento de ajuste de CMV para quantidades já vendidas, com conta '
             'output de stock de cada produto.',
    )

    # ───────────────── Estado ─────────────────
    state = fields.Selection(
        [
            ('draft', 'Rascunho'),
            ('applied', 'Aplicado'),
            ('cancelled', 'Cancelado'),
        ],
        default='draft',
        required=True,
        copy=False,
        tracking=True,
    )
    date = fields.Date(
        string='Data',
        default=fields.Date.today,
        required=True,
        tracking=True,
    )
    notes = fields.Text(string='Notas')

    # ───────────────── Constraints ─────────────────
    _sql_constraints = [
        (
            'unique_invoice_per_import',
            'UNIQUE(import_id, source_invoice_id)',
            'Já existe um ajuste para esta combinação (Importação + Factura).',
        ),
    ]

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.state == 'applied' and rec.amount == 0:
                raise ValidationError(_(
                    "Não pode aplicar um ajuste com valor zero."
                ))

    # ───────────────── CRUD ─────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'ADJ/New') == 'ADJ/New':
                seq = self.env['ir.sequence'].next_by_code('import.document.adjustment')
                vals['name'] = seq or 'ADJ/New'
        return super().create(vals_list)

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_(
                    "Só pode eliminar ajustes em rascunho. "
                    "Cancele primeiro (state='applied' → 'cancelled')."
                ))
        return super().unlink()

    # ───────────────── Acções ─────────────────
    def action_apply(self):
        """Cria 2º Landed Cost + ajuste CMV para qty já vendida."""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Só rascunhos podem ser aplicados."))
        if not self.amount:
            raise UserError(_("Valor zero — nada a aplicar."))
        if not self.import_id.picking_ids:
            raise UserError(_(
                "O Documento de Importação %s não tem pickings — "
                "não é possível distribuir o ajuste."
            ) % self.import_id.name)
        # Validação de configuração: real_time + contas de stock
        # (reutiliza o método do import.document — mesmas regras)
        self.import_id._check_products_configuration()

        # 1) Criar e validar o 2º Landed Cost
        landed_cost = self._create_landed_cost()

        # 2) Para qty já vendida desde IMP done: criar ajuste CMV
        cmv_move = self._create_cmv_adjustment_move(landed_cost)

        # 3) Vincular tudo e finalizar
        self.write({
            'landed_cost_id': landed_cost.id,
            'cmv_adjustment_move_id': cmv_move.id if cmv_move else False,
            'state': 'applied',
        })

        msg_parts = [_("Ajuste aplicado.")]
        msg_parts.append(_("Landed Cost: %s") % landed_cost.name)
        if cmv_move:
            msg_parts.append(_("Ajuste CMV: %s") % cmv_move.name)
        else:
            msg_parts.append(_("Sem ajuste CMV (não há qty vendida no entretanto)."))
        self.message_post(body=Markup("<br/>".join(msg_parts)))
        return True

    def _create_landed_cost(self):
        """Cria stock.landed.cost ligado aos pickings do IMP, com uma cost
        line por linha de factura origem. Compute + validate.

        IMPORTANTE: o `account_id` de cada cost_line é a conta REAL onde o
        valor está lançado na factura (line.account_id). Assim o lançamento
        do LC fica D Stock / C <conta-da-factura>, "transferindo" o custo
        para inventário, em vez de creditar uma conta expense diferente.
        """
        self.ensure_one()
        cost_lines = []
        for line in self.source_invoice_line_ids:
            product = line.product_id
            cost_lines.append((0, 0, {
                'name': line.name or product.display_name,
                'product_id': product.id,
                # balance = valor da linha em moeda da empresa (já convertido ao
                # câmbio da factura). O LC opera em moeda da empresa e credita
                # line.account_id, por isso o balance zera exactamente o lançado.
                'price_unit': line.balance,
                'split_method': product.split_method_landed_cost or 'by_current_cost_price',
                'account_id': line.account_id.id,
            }))

        vals = {
            'picking_ids': [(6, 0, self.import_id.picking_ids.ids)],
            'cost_lines': cost_lines,
            'date': self.date,
        }
        # Diário próprio do LC (não usar o de CMV) — Odoo usa default do company
        landed_cost = self.env['stock.landed.cost'].create(vals)
        landed_cost.compute_landed_cost()
        landed_cost.button_validate()
        return landed_cost

    def _get_cmv_journal(self):
        """Procura diário CMV configurado nos settings."""
        journal_id = self.env['ir.config_parameter'].sudo().get_param(
            'mh_import_adjustment.cmv_journal_id'
        )
        if journal_id:
            try:
                return self.env['account.journal'].browse(int(journal_id)).exists()
            except (ValueError, TypeError):
                pass
        return False

    def _get_origin_account(self):
        """Conta da factura origem (contrapartida do ajuste CMV)."""
        self.ensure_one()
        accounts = self.source_invoice_line_ids.mapped('account_id')
        if not accounts:
            return False
        if len(accounts) > 1:
            _logger.warning(
                "ADJ %s: linhas-origem em múltiplas contas (%s) — usando a primeira.",
                self.name, accounts.mapped('code'),
            )
        return accounts[0]

    def _get_qty_sold_since(self, product, lot_group_ids, lot_ids, date_from):
        """Retorna qty vendida (SVL outgoing) desde date_from para o produto.

        Filtragem por ordem de precisão:
          1. lot_group_id  — se modelo tem o campo (Stone, base.lot.group)
                             e há lot_groups associados ao IMP
          2. lot_id        — lote individual (fallback)
          3. só produto+data — fallback final (produtos sem lots)
        """
        domain = [
            ('product_id', '=', product.id),
            ('quantity', '<', 0),
            ('create_date', '>=', date_from),
        ]
        has_lot_group = 'lot_group_id' in self.env['stock.valuation.layer']._fields
        if has_lot_group and lot_group_ids:
            domain.append(('lot_group_id', 'in', lot_group_ids))
        elif lot_ids:
            domain.append(('lot_id', 'in', lot_ids))
        svls = self.env['stock.valuation.layer'].search(domain)
        return -sum(svls.mapped('quantity'))  # negativo → positivo

    def _create_cmv_adjustment_move(self, landed_cost):
        """Cria account.move ajuste CMV para qty vendida desde IMP done.

        Para cada produto com qty vendida desde IMP done:
          D = stock_output_account do produto/categoria   (reconhece CMV extra)
          C = stock_valuation_account do produto          (retira do stock book)

        Esta contrapartida (stock_valuation, não origin_account) é necessária
        porque o standard Odoo LC já zera a origin_account creditando-a no
        total. As qty já vendidas têm a parte do LC sobre-imputada em
        Existências — este ajuste transfere-a para CMV.

        Se nenhuma qty foi vendida, retorna False.
        """
        self.ensure_one()
        imp_done_date = self.import_id.reception_date or self.import_id.date
        if not imp_done_date:
            return False

        journal = self._get_cmv_journal()
        if not journal:
            raise UserError(_(
                "Diário de Ajuste CMV não configurado. "
                "Vai a Configurações → Contabilidade e define 'Diário de Ajuste CMV (Importações)'."
            ))

        SVL = self.env['stock.valuation.layer']
        has_lot_group = 'lot_group_id' in SVL._fields

        # Agregar valuation_adjustment_lines POR (PRODUTO, LOT_GROUP).
        #
        # Razão para agregar por lot_group também (e não só produto):
        #   Em PCMP Stone, o pool de valorização é por base.lot.group.
        #   Vendas saem de um lot_group específico; o ajuste CMV tem de afectar
        #   esse mesmo lot_group, não o produto inteiro.
        #
        # Em Pemaro (sem lot_group_id), o key colapsa para (product, False),
        # comportando-se como agregação por produto pura.
        per_pg = {}  # (product.id, lot_group_id_or_False) → entry
        for adj_line in landed_cost.valuation_adjustment_lines:
            product = adj_line.product_id
            picking_qty = adj_line.quantity
            if not picking_qty:
                continue
            # lot_group_id via SVL IN deste stock_move
            lg_id = False
            if has_lot_group:
                entry_svl = adj_line.move_id.stock_valuation_layer_ids.filtered(
                    lambda l: l.quantity > 0
                )[:1]
                lg_id = entry_svl.lot_group_id.id if entry_svl and entry_svl.lot_group_id else False
            key = (product.id, lg_id)
            entry = per_pg.setdefault(key, {
                'product': product,
                'lot_group_id': lg_id,
                'total_qty': 0.0,
                'total_lc': 0.0,
            })
            entry['total_qty'] += picking_qty
            entry['total_lc'] += adj_line.additional_landed_cost

        move_lines = []
        svl_specs = []  # (product, lot_group_id, cmv_amount, label)

        for entry in per_pg.values():
            product = entry['product']
            lot_group_id = entry['lot_group_id']
            total_qty = entry['total_qty']
            total_lc = entry['total_lc']
            if not total_qty:
                continue
            unit_cost_added = total_lc / total_qty

            # Filtro da qty vendida:
            #   - Se há lot_group: filtrar por ESSE lot_group (precisão Stone)
            #   - Senão: lots individuais dos pickings (fallback)
            lot_group_ids = [lot_group_id] if (has_lot_group and lot_group_id) else []
            lot_ids = []
            if not lot_group_ids:
                lot_ids = self.import_id.picking_ids.move_ids.move_line_ids.filtered(
                    lambda ml: ml.product_id == product
                ).mapped('lot_id').ids

            # Buscar SVLs OUT directamente (em vez de só somar qty) para
            # podermos popular o adjusted_unit_cost nos stock.moves
            domain = [
                ('product_id', '=', product.id),
                ('quantity', '<', 0),
                ('create_date', '>=', imp_done_date),
            ]
            if has_lot_group and lot_group_ids:
                domain.append(('lot_group_id', 'in', lot_group_ids))
            elif lot_ids:
                domain.append(('lot_id', 'in', lot_ids))
            out_svls = SVL.search(domain)
            sold_qty = -sum(out_svls.mapped('quantity'))

            # Subtrair devoluções (RETs) feitas antes da aplicação do ADJ.
            # As RETs entraram ao custo pré-ADJ e estão de volta em stock; não
            # devem ser contabilizadas como "vendidas" para efeitos de CMV.
            # Padrão alinhado com mh_purchase._calculate_provisional_sales:
            # qty>0 + stock_move_id, depois exclui os moves de entrada do IMP.
            ret_domain = [
                ('product_id', '=', product.id),
                ('quantity', '>', 0),
                ('create_date', '>=', imp_done_date),
                ('stock_move_id', '!=', False),
            ]
            if has_lot_group and lot_group_ids:
                ret_domain.append(('lot_group_id', 'in', lot_group_ids))
            elif lot_ids:
                ret_domain.append(('lot_id', 'in', lot_ids))
            ret_svls = SVL.search(ret_domain)
            entry_move_ids = self.import_id.picking_ids.move_ids.ids
            ret_svls = ret_svls.filtered(lambda s: s.stock_move_id.id not in entry_move_ids)
            returned_qty = sum(ret_svls.mapped('quantity'))

            net_sold = sold_qty - returned_qty
            if net_sold <= 0:
                continue

            # Popular adjusted_unit_cost no stock.move de cada OUT afectado
            # (acumula se já tinha ADJ anterior). Usado por _get_price_unit
            # para garantir que devoluções entram ao custo real (não histórico).
            for out_svl in out_svls:
                out_move = out_svl.stock_move_id
                if not out_move:
                    continue
                if out_move.adjusted_unit_cost:
                    out_move.adjusted_unit_cost += unit_cost_added
                else:
                    original_uc = abs(out_svl.unit_cost) or (
                        abs(out_svl.value) / abs(out_svl.quantity)
                        if out_svl.quantity else 0.0
                    )
                    out_move.adjusted_unit_cost = original_uc + unit_cost_added

            cmv_amount = net_sold * unit_cost_added
            accounts = product.product_tmpl_id.get_product_accounts()
            stock_output = accounts.get('stock_output')
            stock_valuation = accounts.get('stock_valuation')

            if not stock_output:
                _logger.warning(
                    "ADJ %s: produto %s sem stock_output_account, saltando.",
                    self.name, product.display_name,
                )
                continue
            if not stock_valuation:
                _logger.warning(
                    "ADJ %s: produto %s sem stock_valuation_account, saltando.",
                    self.name, product.display_name,
                )
                continue

            label = _("Ajuste CMV %s") % product.display_name
            move_lines.append((0, 0, {
                'name': label,
                'product_id': product.id,
                'account_id': stock_output.id,
                'debit': cmv_amount,
                'credit': 0.0,
            }))
            move_lines.append((0, 0, {
                'name': label,
                'product_id': product.id,
                'account_id': stock_valuation.id,
                'debit': 0.0,
                'credit': cmv_amount,
            }))
            svl_specs.append((product, lot_group_id, cmv_amount, label))

        if not move_lines:
            return False

        move = self.env['account.move'].create({
            'move_type': 'entry',
            'date': self.date,
            'journal_id': journal.id,
            'ref': _("Ajuste CMV %s ← %s") % (self.name, self.source_invoice_id.name),
            'line_ids': move_lines,
        })
        move.action_post()

        # Criar SVL por (produto, lot_group) — alinha pool de cada lot_group
        # com a contabilidade.
        SVL_sudo = SVL.sudo()
        for product, lot_group_id, cmv_amount, label in svl_specs:
            svl_vals = {
                'company_id': self.company_id.id,
                'product_id': product.id,
                'quantity': 0.0,
                'unit_cost': 0.0,
                'value': -cmv_amount,
                'description': label,
                'account_move_id': move.id,
            }
            if has_lot_group and lot_group_id:
                svl_vals['lot_group_id'] = lot_group_id
            SVL_sudo.create(svl_vals)

        return move

    def action_cancel(self):
        for rec in self:
            if rec.state == 'applied':
                raise UserError(_(
                    "Ajuste aplicado não pode ser cancelado.\n\n"
                    "Os documentos contabilísticos (Landed Cost %(lc)s e Ajuste CMV %(cmv)s) "
                    "já foram lançados e fazem parte do histórico fiscal.\n\n"
                    "Para inverter o efeito, crie um novo ajuste com valor oposto."
                ) % {
                    'lc': rec.landed_cost_id.name or '—',
                    'cmv': rec.cmv_adjustment_move_id.name or '—',
                })
            rec.state = 'cancelled'

    def action_reset_draft(self):
        for rec in self:
            if rec.state != 'cancelled':
                raise UserError(_("Só ajustes cancelados podem voltar a rascunho."))
            rec.state = 'draft'

    def action_view_landed_cost(self):
        self.ensure_one()
        if not self.landed_cost_id:
            raise UserError(_("Nenhum Landed Cost associado."))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.landed.cost',
            'view_mode': 'form',
            'res_id': self.landed_cost_id.id,
        }

    def action_view_cmv_move(self):
        self.ensure_one()
        if not self.cmv_adjustment_move_id:
            raise UserError(_("Nenhum ajuste CMV associado."))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.cmv_adjustment_move_id.id,
        }

    def action_view_source_invoice(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.source_invoice_id.id,
        }
