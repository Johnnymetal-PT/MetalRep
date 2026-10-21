# -*- coding: utf-8 -*-

import base64
import io
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

try:
    import openpyxl
    OPENPYXL_INSTALLED = True
except ImportError:
    OPENPYXL_INSTALLED = False


class CashImportWizard(models.TransientModel):
    _name = 'cash.import.wizard'
    _description = 'Wizard para Importar Extracto de Caixa'

    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Diário de Caixa',
        required=True,
        domain=[('type', '=', 'cash')],
    )
    data_file = fields.Binary(
        string='Ficheiro Excel',
        help='Ficheiro Excel (.xlsx) com os movimentos a importar.',
    )
    filename = fields.Char(
        string='Nome do Ficheiro',
    )
    import_mode = fields.Selection([
        ('statement_line', 'Criar Linhas de Extracto'),
        ('reconcile_direct', 'Reconciliar Directamente (por ID)'),
    ], string='Modo de Importação', default='statement_line', required=True,
       help='Linhas de Extracto: Cria linhas para reconciliar manualmente.\n'
            'Reconciliar Directamente: Usa o ID do movimento para marcar como reconciliado.')

    # Campos do Extracto (Statement)
    statement_name = fields.Char(
        string='Referência do Extracto',
        required=True,
        help='Nome/referência do extracto. Ex: "Fecho Caixa 02/01/2026"',
    )
    statement_date = fields.Date(
        string='Data do Extracto',
        default=fields.Date.context_today,
        required=True,
    )
    excel_opening_balance = fields.Monetary(
        string='Saldo Inicial (Extracto)',
        currency_field='currency_id',
        readonly=True,
        help='Saldo inicial extraído do ficheiro Excel.',
    )
    excel_closing_balance = fields.Monetary(
        string='Saldo Final (Extracto)',
        currency_field='currency_id',
        readonly=True,
        help='Saldo final extraído do ficheiro Excel.',
    )
    balance_start = fields.Monetary(
        string='Saldo Inicial',
        currency_field='currency_id',
        compute='_compute_balance_start',
        store=True,
        readonly=False,
        help='Saldo inicial do caixa (automático do extracto anterior ou manual).',
    )
    balance_end_real = fields.Monetary(
        string='Saldo Final (Contado)',
        currency_field='currency_id',
        help='Saldo final contado fisicamente no caixa.',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Moeda',
        compute='_compute_currency_id',
    )
    balance_end_computed = fields.Monetary(
        string='Saldo Final (Calculado)',
        currency_field='currency_id',
        compute='_compute_balance_end',
        help='Saldo calculado: Saldo Inicial + Σ Transações',
    )
    balance_difference = fields.Monetary(
        string='Diferença',
        currency_field='currency_id',
        compute='_compute_balance_difference',
        help='Diferença entre saldo contado e calculado (sobra/falta).',
    )

    # Campos para resultado
    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('preview', 'Pré-visualização'),
        ('done', 'Concluído'),
    ], default='draft')
    preview_line_ids = fields.One2many(
        comodel_name='cash.import.preview.line',
        inverse_name='wizard_id',
        string='Linhas a Importar',
    )
    import_count = fields.Integer(
        string='Linhas Importadas',
        readonly=True,
    )
    error_message = fields.Text(
        string='Erros',
        readonly=True,
    )

    @api.constrains('data_file', 'filename')
    def _check_file_extension(self):
        """Valida que o ficheiro é Excel."""
        for wizard in self:
            if wizard.filename and not wizard.filename.lower().endswith(('.xlsx', '.xls')):
                raise ValidationError(_('Por favor carregue um ficheiro Excel (.xlsx ou .xls).'))

    @api.depends('journal_id')
    def _compute_currency_id(self):
        """Obtém a moeda do diário."""
        for wizard in self:
            wizard.currency_id = wizard.journal_id.currency_id or wizard.journal_id.company_id.currency_id

    @api.depends('journal_id')
    def _compute_balance_start(self):
        """Calcula o saldo inicial baseado no último extracto do diário."""
        for wizard in self:
            if wizard.journal_id:
                # Buscar o último extracto do diário
                last_statement = self.env['account.bank.statement'].search([
                    ('journal_id', '=', wizard.journal_id.id),
                ], order='date desc, id desc', limit=1)

                if last_statement:
                    wizard.balance_start = last_statement.balance_end_real
                else:
                    # Se não há extracto anterior, buscar saldo da conta do diário
                    wizard.balance_start = 0.0
            else:
                wizard.balance_start = 0.0

    @api.depends('balance_start', 'preview_line_ids', 'preview_line_ids.amount', 'preview_line_ids.to_import')
    def _compute_balance_end(self):
        """Calcula o saldo final: saldo inicial + soma das transações."""
        for wizard in self:
            total_amount = sum(
                line.amount for line in wizard.preview_line_ids if line.to_import
            )
            wizard.balance_end_computed = wizard.balance_start + total_amount

    @api.depends('balance_end_real', 'balance_end_computed')
    def _compute_balance_difference(self):
        """Calcula a diferença entre saldo contado e calculado."""
        for wizard in self:
            if wizard.balance_end_real:
                wizard.balance_difference = wizard.balance_end_real - wizard.balance_end_computed
            else:
                wizard.balance_difference = 0.0

    def action_preview(self):
        """Pré-visualiza os dados do Excel antes de importar."""
        self.ensure_one()

        if not OPENPYXL_INSTALLED:
            raise UserError(_('A biblioteca openpyxl não está instalada. Por favor instale com: pip install openpyxl'))

        if not self.data_file:
            raise UserError(_('Por favor carregue um ficheiro Excel.'))

        # Ler ficheiro Excel
        try:
            file_content = base64.b64decode(self.data_file)
            workbook = openpyxl.load_workbook(io.BytesIO(file_content), data_only=True)
            worksheet = workbook.active
        except Exception as e:
            raise UserError(_('Erro ao ler o ficheiro Excel: %s') % str(e))

        # Limpar linhas anteriores
        self.preview_line_ids.unlink()

        # Processar linhas (ignorar cabeçalho)
        preview_lines = []
        errors = []
        row_num = 0
        excel_opening_balance = 0.0
        excel_closing_balance = 0.0

        for row in worksheet.iter_rows(min_row=2, values_only=True):
            row_num += 1

            # Ignorar linhas completamente vazias
            if not row:
                continue

            # Verificar se é linha de total, info, cabeçalho ou saldo
            first_cell = str(row[0]).strip() if row[0] else ''
            third_cell = str(row[2]).strip().upper() if len(row) > 2 and row[2] else ''

            # Extrair saldo inicial do Excel (coluna 3 = "SALDO INICIAL", coluna 7 = valor)
            if third_cell == 'SALDO INICIAL':
                try:
                    excel_opening_balance = float(row[6]) if row[6] else 0.0
                except (ValueError, TypeError):
                    excel_opening_balance = 0.0
                continue

            # Extrair saldo final do Excel
            if third_cell == 'SALDO FINAL':
                try:
                    excel_closing_balance = float(row[6]) if row[6] else 0.0
                except (ValueError, TypeError):
                    excel_closing_balance = 0.0
                continue

            # Ignorar linhas sem data na primeira coluna (linhas especiais)
            if not row[0]:
                continue

            # Ignorar linhas especiais (cabeçalhos, totais, resumo, legenda)
            if (first_cell.upper() in ('TOTAL:', 'INFORMAÇÕES:', 'INFORMACOES:', 'DATA', 'LEGENDA:') or
                first_cell.startswith('Diário:') or
                first_cell.startswith('EXTRACTO') or
                first_cell.startswith('Período:') or
                first_cell.startswith('Saldo Inicial:') or
                first_cell.startswith('(+)') or
                first_cell.startswith('(-)') or
                first_cell.startswith('=') or
                first_cell.startswith('■') or
                first_cell.startswith('Exportado em:') or
                third_cell in ('SUBTOTAL CONFIRMADOS:', 'SUBTOTAL PENDENTES:') or
                'MOVIMENTOS CONFIRMADOS' in first_cell.upper() or
                'MOVIMENTOS PENDENTES' in first_cell.upper() or
                'RESUMO' in first_cell.upper()):
                continue

            try:
                # Formato do Excel: Data, Referência, Descrição, Parceiro, Entrada, Saída, Saldo, Estado, ID
                date_val = row[0]
                ref = str(row[1]).strip() if row[1] else ''
                name = str(row[2]).strip() if row[2] else ref
                partner_name = str(row[3]).strip() if row[3] else ''
                # Entrada = Débito (dinheiro entra no caixa)
                entrada = float(row[4]) if row[4] and str(row[4]).replace('.', '').replace(',', '').isdigit() else 0.0
                # Saída = Crédito (dinheiro sai do caixa)
                saida = float(row[5]) if row[5] and str(row[5]).replace('.', '').replace(',', '').isdigit() else 0.0
                # Saldo acumulado (coluna 6)
                try:
                    balance = float(row[6]) if row[6] else 0.0
                except (ValueError, TypeError):
                    balance = 0.0
                reconciled_str = str(row[7]).strip().lower() if len(row) > 7 and row[7] else 'não'
                move_line_id = int(row[8]) if len(row) > 8 and row[8] else 0

                # Usar entrada/saída como débito/crédito
                debit = entrada
                credit = saida

                # Converter data
                if isinstance(date_val, datetime):
                    date_parsed = date_val.date()
                elif isinstance(date_val, str):
                    # Tentar formatos comuns
                    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d'):
                        try:
                            date_parsed = datetime.strptime(date_val, fmt).date()
                            break
                        except ValueError:
                            continue
                    else:
                        raise ValueError(f'Formato de data inválido: {date_val}')
                else:
                    date_parsed = date_val

                # Determinar se é confirmado (já no caixa) ou pendente
                # Coluna Estado pode ter: "Confirmado", "Pendente", "Sim", "Não"
                is_confirmed = reconciled_str in ('confirmado', 'confirmed', 'sim', 'yes', 's', 'y', 'true', '1')

                # Buscar parceiro
                partner_id = False
                if partner_name:
                    partner = self.env['res.partner'].search([
                        '|',
                        ('name', 'ilike', partner_name),
                        ('display_name', 'ilike', partner_name),
                    ], limit=1)
                    partner_id = partner.id if partner else False

                # Calcular amount (débito - crédito)
                # Débito em Outstanding Receipts = entrada (+)
                # Crédito em Outstanding Payments = saída (-)
                amount = debit - credit

                # Criar linha de preview
                preview_lines.append({
                    'wizard_id': self.id,
                    'row_number': row_num + 1,
                    'date': date_parsed,
                    'payment_ref': ref or name,
                    'name': name,
                    'partner_name': partner_name,
                    'partner_id': partner_id,
                    'debit': debit,      # Entrada
                    'credit': credit,    # Saída
                    'amount': amount,    # Entrada - Saída
                    'balance': balance,  # Saldo acumulado do Excel
                    'is_reconciled': is_confirmed,
                    'move_line_id': move_line_id,
                    'to_import': not is_confirmed,  # Por defeito, importar apenas PENDENTES (não confirmados)
                })

            except Exception as e:
                errors.append(f'Linha {row_num + 1}: {str(e)}')

        # Criar linhas de preview
        if preview_lines:
            self.env['cash.import.preview.line'].create(preview_lines)

        # Atualizar estado
        self.write({
            'state': 'preview',
            'excel_opening_balance': excel_opening_balance,
            'excel_closing_balance': excel_closing_balance,
            'error_message': '\n'.join(errors) if errors else False,
        })

        return {
            'name': _('Fecho de Caixa - Confirmar Pendentes'),
            'type': 'ir.actions.act_window',
            'res_model': 'cash.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_import(self):
        """Importa as linhas selecionadas criando um extracto bancário."""
        self.ensure_one()

        if not self.preview_line_ids:
            raise UserError(_('Não há linhas para importar. Por favor faça a pré-visualização primeiro.'))

        lines_to_import = self.preview_line_ids.filtered(lambda l: l.to_import)

        if not lines_to_import:
            raise UserError(_('Nenhuma linha selecionada para importar. Marque as linhas que deseja importar.'))

        if not self.balance_end_real:
            raise UserError(_('Por favor introduza o Saldo Final (Contado) - o valor contado fisicamente no caixa.'))

        # Criar o extracto bancário (account.bank.statement)
        statement_name = self.statement_name or _('Fecho Caixa %s') % self.statement_date.strftime('%d/%m/%Y')

        statement = self.env['account.bank.statement'].create({
            'name': statement_name,
            'date': self.statement_date,
            'journal_id': self.journal_id.id,
            'balance_start': self.balance_start,
            'balance_end_real': self.balance_end_real,
        })

        created_lines = self.env['account.bank.statement.line']
        errors = []

        for line in lines_to_import:
            try:
                statement_line = self.env['account.bank.statement.line'].create({
                    'statement_id': statement.id,
                    'date': line.date,
                    'payment_ref': line.payment_ref or line.name,
                    'amount': line.amount,
                    'partner_id': line.partner_id.id if line.partner_id else False,
                    'journal_id': self.journal_id.id,
                })
                created_lines |= statement_line

            except Exception as e:
                errors.append(f'Linha {line.row_number}: {str(e)}')

        # Atualizar estado
        self.write({
            'state': 'done',
            'import_count': len(created_lines),
            'error_message': '\n'.join(errors) if errors else False,
        })

        # Abrir o extracto criado
        if created_lines:
            return {
                'name': _('Extracto de Caixa'),
                'type': 'ir.actions.act_window',
                'res_model': 'account.bank.statement',
                'res_id': statement.id,
                'view_mode': 'form',
                'target': 'current',
            }

        return {
            'name': _('Fecho de Caixa - Confirmar Pendentes'),
            'type': 'ir.actions.act_window',
            'res_model': 'cash.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_back_to_draft(self):
        """Volta ao estado inicial para carregar novo ficheiro."""
        self.ensure_one()
        self.preview_line_ids.unlink()
        self.write({
            'state': 'draft',
            'error_message': False,
            'import_count': 0,
        })
        return {
            'name': _('Fecho de Caixa - Confirmar Pendentes'),
            'type': 'ir.actions.act_window',
            'res_model': 'cash.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }


class CashImportPreviewLine(models.TransientModel):
    _name = 'cash.import.preview.line'
    _description = 'Linha de Pré-visualização para Importação'

    wizard_id = fields.Many2one(
        comodel_name='cash.import.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade',
    )
    row_number = fields.Integer(
        string='Linha',
    )
    to_import = fields.Boolean(
        string='Importar',
        default=True,
    )
    date = fields.Date(
        string='Data',
    )
    payment_ref = fields.Char(
        string='Referência',
    )
    name = fields.Char(
        string='Descrição',
    )
    partner_name = fields.Char(
        string='Nome Parceiro',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Parceiro',
    )
    debit = fields.Float(
        string='Entrada',
        help='Dinheiro que entra no caixa',
    )
    credit = fields.Float(
        string='Saída',
        help='Dinheiro que sai do caixa',
    )
    amount = fields.Float(
        string='Valor',
        help='Entrada - Saída (positivo = entrada, negativo = saída)',
    )
    balance = fields.Float(
        string='Saldo',
        help='Saldo acumulado extraído do Excel.',
    )
    is_reconciled = fields.Boolean(
        string='Reconciliado',
        help='Se já está marcado como reconciliado no Excel.',
    )
    move_line_id = fields.Integer(
        string='ID Movimento',
        help='ID do account.move.line original (se exportado deste sistema).',
    )
