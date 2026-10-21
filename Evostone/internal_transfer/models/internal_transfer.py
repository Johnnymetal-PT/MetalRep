# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class InternalTransfer(models.Model):
    _name = 'internal.transfer'
    _description = 'Transferência Interna'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'data desc, id desc'

    name = fields.Char(
        string='Referência',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        required=True,
        default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Moeda',
        related='company_id.currency_id',
        store=True
    )
    data = fields.Date(
        string='Data',
        required=True,
        default=fields.Date.context_today
    )
    origem = fields.Many2one(
        'account.journal',
        string='Diário Origem',
        required=True,
        domain="[('type', 'in', ['bank', 'cash']), ('company_id', '=', company_id)]"
    )
    destino = fields.Many2one(
        'account.journal',
        string='Diário Destino',
        required=True,
        domain="[('type', 'in', ['bank', 'cash']), ('company_id', '=', company_id)]"
    )
    valor = fields.Monetary(
        string='Valor',
        required=True,
        currency_field='currency_id'
    )
    memorando = fields.Text(string='Memorando')
    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('posted', 'Publicada'),
        ('cancelled', 'Cancelada'),
    ], string='Estado', default='draft', tracking=True)

    # Contas de transferência
    transfer_account_id = fields.Many2one(
        'account.account',
        string='Conta de Transferência',
        compute='_compute_transfer_accounts',
        store=True,
        help='Conta 12404 - Transferência Interna'
    )
    outstanding_receipts_account_id = fields.Many2one(
        'account.account',
        string='Conta Recebimentos Pendentes',
        compute='_compute_transfer_accounts',
        store=True,
        help='Conta 12402 - Recebimentos Pendentes (usada no destino)'
    )
    outstanding_payments_account_id = fields.Many2one(
        'account.account',
        string='Conta Pagamentos Pendentes',
        compute='_compute_transfer_accounts',
        store=True,
        help='Conta 12403 - Pagamentos Pendentes (usada na origem)'
    )

    # Lançamentos contabilísticos
    move_ids = fields.Many2many(
        'account.move',
        'internal_transfer_move_rel',
        'transfer_id',
        'move_id',
        string='Lançamentos Contabilísticos'
    )
    move_count = fields.Integer(
        string='Contagem de Lançamentos',
        compute='_compute_move_count'
    )

    @api.depends('company_id')
    def _compute_transfer_accounts(self):
        """Obtém as contas de transferência da configuração"""
        IrConfigParam = self.env['ir.config_parameter'].sudo()

        for record in self:
            record.transfer_account_id = False
            record.outstanding_receipts_account_id = False
            record.outstanding_payments_account_id = False

            # Conta 12404 - Transferência Interna
            config_transfer = IrConfigParam.get_param('internal_transfer.transfer_account_id')
            if config_transfer:
                account = self.env['account.account'].browse(int(config_transfer))
                if account.exists() and record.company_id in account.company_ids:
                    record.transfer_account_id = account

            # Conta 12402 - Recebimentos Pendentes
            config_receipts = IrConfigParam.get_param('internal_transfer.outstanding_receipts_account_id')
            if config_receipts:
                account = self.env['account.account'].browse(int(config_receipts))
                if account.exists() and record.company_id in account.company_ids:
                    record.outstanding_receipts_account_id = account

            # Conta 12403 - Pagamentos Pendentes
            config_payments = IrConfigParam.get_param('internal_transfer.outstanding_payments_account_id')
            if config_payments:
                account = self.env['account.account'].browse(int(config_payments))
                if account.exists() and record.company_id in account.company_ids:
                    record.outstanding_payments_account_id = account

    def _compute_move_count(self):
        for rec in self:
            rec.move_count = len(rec.move_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('internal.transfer') or _('New')
        return super().create(vals_list)

    def unlink(self):
        """Impedir eliminação de transferências"""
        for record in self:
            raise UserError(_('Não é permitido eliminar transferências internas. Use o botão Cancelar se necessário.'))
        return super().unlink()

    def _check_date_order(self):
        """Data não-decrescente por ordem de criação: >= à publicada criada antes,
        e <= à publicada criada depois desta."""
        for record in self:
            if not record.data:
                continue
            last = self.search([
                ('state', '=', 'posted'),
                ('company_id', '=', record.company_id.id),
                ('id', '<', record.id),
            ], order='id desc', limit=1)
            if last and record.data < last.data:
                raise ValidationError(_(
                    'Não é possível publicar com data %(data)s: é anterior à data '
                    'da última transferência publicada (%(ref)s — %(ult)s).'
                ) % {
                    'data': record.data.strftime('%d/%m/%Y'),
                    'ref': last.name,
                    'ult': last.data.strftime('%d/%m/%Y'),
                })
            nxt = self.search([
                ('state', '=', 'posted'),
                ('company_id', '=', record.company_id.id),
                ('id', '>', record.id),
            ], order='id asc', limit=1)
            if nxt and record.data > nxt.data:
                raise ValidationError(_(
                    'Não é possível publicar com data %(data)s: é posterior à data '
                    'da transferência seguinte (%(ref)s — %(seg)s).'
                ) % {
                    'data': record.data.strftime('%d/%m/%Y'),
                    'ref': nxt.name,
                    'seg': nxt.data.strftime('%d/%m/%Y'),
                })

    @api.constrains('data', 'state')
    def _constrain_date_order(self):
        """Fecha a brecha: valida em qualquer write (não só no botão Publicar)."""
        self.filtered(lambda r: r.state == 'posted')._check_date_order()

    def action_post(self):
        """Publicar a transferência - cria os lançamentos contabilísticos"""
        for record in self:
            if record.state != 'draft':
                continue

            # Validações
            record._check_date_order()
            if record.origem == record.destino:
                raise UserError(_('O diário de origem e destino não podem ser iguais.'))
            if record.valor <= 0:
                raise UserError(_('O valor deve ser maior que zero.'))
            if not record.transfer_account_id:
                raise UserError(_(
                    'Conta de Transferência Interna (12404) não configurada.\n\n'
                    'Configure em: Contabilidade → Configurações → Transferências Internas'
                ))
            if not record.outstanding_payments_account_id:
                raise UserError(_(
                    'Conta de Pagamentos Pendentes (12403) não configurada.\n\n'
                    'Configure em: Contabilidade → Configurações → Transferências Internas'
                ))
            if not record.outstanding_receipts_account_id:
                raise UserError(_(
                    'Conta de Recebimentos Pendentes (12402) não configurada.\n\n'
                    'Configure em: Contabilidade → Configurações → Transferências Internas'
                ))

            # Criar os lançamentos
            record._create_account_moves()
            record.state = 'posted'

    def _check_moves_not_reconciled_with_bank(self):
        """Bloqueia se algum dos moves da transferência estiver reconciliado
        com linhas de extracto bancário. Obriga o utilizador a anular primeiro
        a reconciliação na linha do extracto. Acumula TODOS os bloqueios numa
        única mensagem."""
        self.ensure_one()
        blocks = []
        for move in self.move_ids:
            if not hasattr(move, '_get_bank_statement_reconciled_lines'):
                continue
            other_lines = move._get_bank_statement_reconciled_lines()
            if not other_lines:
                continue
            for sl in other_lines.move_id.statement_line_id:
                blocks.append(
                    f"  • {move.display_name} ↔ Extracto {sl.journal_id.name} — "
                    f"linha de {sl.date.strftime('%d/%m/%Y')}: "
                    f"{sl.payment_ref or ''} ({sl.amount:.2f} {sl.currency_id.name})"
                )
        if blocks:
            raise UserError(_(
                "Não é possível alterar a transferência %(name)s porque os seguintes "
                "lançamentos estão reconciliados com extracto(s) bancário(s):\n%(details)s\n\n"
                "Anule primeiro a reconciliação na(s) linha(s) do extracto e tente novamente."
            ) % {
                'name': self.name,
                'details': '\n'.join(blocks),
            })

    def action_draft(self):
        """Voltar a rascunho — cancela os lançamentos contabilísticos e
        desvincula-os da transferência, preservando os números de sequência
        do diário (não apaga os moves)."""
        for record in self:
            if record.state not in ('posted', 'cancelled'):
                continue

            # Bloquear se houver reconciliação com extracto bancário
            record._check_moves_not_reconciled_with_bank()

            for move in record.move_ids:
                # Desfazer reconciliação interna (12404 - Transferência Interna)
                for line in move.line_ids.filtered(lambda l: l.reconciled):
                    line.remove_move_reconcile()
                # Garantir estado 'cancel' (sem apagar — preserva sequência)
                if move.state == 'posted':
                    move.button_draft()
                if move.state == 'draft':
                    move.button_cancel()

            # Desvincular os moves (eles permanecem em account.move como cancelados)
            record.move_ids = [(5, 0, 0)]
            record.state = 'draft'

    def action_cancel(self):
        """Cancelar a transferência — cancela os lançamentos contabilísticos
        associados (passam a estado 'cancel', preservando a numeração)."""
        for record in self:
            if record.state == 'cancelled':
                continue

            if record.state == 'posted':
                # Bloquear se houver reconciliação com extracto bancário
                record._check_moves_not_reconciled_with_bank()

                for move in record.move_ids:
                    # Desfazer reconciliação interna (12404 - Transferência Interna)
                    for line in move.line_ids.filtered(lambda l: l.reconciled):
                        line.remove_move_reconcile()
                    # Posted → Draft → Cancel
                    if move.state == 'posted':
                        move.button_draft()
                    if move.state == 'draft':
                        move.button_cancel()

            record.state = 'cancelled'

    def _create_account_moves(self):
        """
        Cria os lançamentos contabilísticos para a transferência.

        Padrão contabilístico Odoo 18:
        - Lançamento 1 (Diário Origem): Crédito 12403 Pagamentos Pendentes, Débito 12404 Transferência Interna
        - Lançamento 2 (Diário Destino): Débito 12402 Recebimentos Pendentes, Crédito 12404 Transferência Interna

        A reconciliação é feita manualmente nos diários quando o utilizador importa extractos bancários.
        """
        self.ensure_one()
        AccountMove = self.env['account.move']

        # Lançamento 1: Saída do diário origem
        # Crédito 12403 Pagamentos Pendentes + Débito 12404 Transferência Interna
        move_origem = AccountMove.create({
            'move_type': 'entry',
            'date': self.data,
            'journal_id': self.origem.id,
            'ref': f'Transferência Interna {self.name} - Saída',
            'narration': self.memorando,
            'checked': True,
            'line_ids': [
                (0, 0, {
                    'name': f'Transferência para {self.destino.name}',
                    'account_id': self.outstanding_payments_account_id.id,
                    'credit': self.valor,
                    'debit': 0,
                }),
                (0, 0, {
                    'name': f'Transferência para {self.destino.name}',
                    'account_id': self.transfer_account_id.id,
                    'debit': self.valor,
                    'credit': 0,
                }),
            ]
        })

        # Lançamento 2: Entrada no diário destino
        # Débito 12402 Recebimentos Pendentes + Crédito 12404 Transferência Interna
        move_destino = AccountMove.create({
            'move_type': 'entry',
            'date': self.data,
            'journal_id': self.destino.id,
            'ref': f'Transferência Interna {self.name} - Entrada',
            'narration': self.memorando,
            'checked': True,
            'line_ids': [
                (0, 0, {
                    'name': f'Transferência de {self.origem.name}',
                    'account_id': self.transfer_account_id.id,
                    'credit': self.valor,
                    'debit': 0,
                }),
                (0, 0, {
                    'name': f'Transferência de {self.origem.name}',
                    'account_id': self.outstanding_receipts_account_id.id,
                    'debit': self.valor,
                    'credit': 0,
                }),
            ]
        })

        # Publicar os lançamentos
        move_origem.action_post()
        move_destino.action_post()

        # Associar lançamentos à transferência
        self.move_ids = [(6, 0, [move_origem.id, move_destino.id])]

        # Reconciliar as linhas da conta 12404 (Transferência Interna)
        # Débito da origem + Crédito do destino
        lines_to_reconcile = (move_origem.line_ids + move_destino.line_ids).filtered(
            lambda l: l.account_id == self.transfer_account_id
        )
        if len(lines_to_reconcile) == 2:
            lines_to_reconcile.reconcile()

    def action_view_moves(self):
        """Acção para ver os lançamentos contabilísticos"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Lançamentos Contabilísticos'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.move_ids.ids)],
            'context': {'create': False},
        }

    @api.onchange('origem')
    def _onchange_origem(self):
        """Limpar destino se igual à origem"""
        if self.origem and self.destino and self.origem == self.destino:
            self.destino = False

    @api.onchange('destino')
    def _onchange_destino(self):
        """Validar que destino é diferente de origem"""
        if self.origem and self.destino and self.origem == self.destino:
            return {
                'warning': {
                    'title': _('Aviso'),
                    'message': _('O diário de destino não pode ser igual ao de origem.')
                }
            }
