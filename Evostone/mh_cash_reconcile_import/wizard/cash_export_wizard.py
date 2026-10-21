# -*- coding: utf-8 -*-

import base64
import io
from datetime import date, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError

try:
    import openpyxl
    from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
    from openpyxl.utils import get_column_letter
    OPENPYXL_INSTALLED = True
except ImportError:
    OPENPYXL_INSTALLED = False


class CashExportWizard(models.TransientModel):
    _name = 'cash.export.wizard'
    _description = 'Wizard para Exportar Movimentos de Caixa'

    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Diário de Caixa',
        required=True,
        domain=[('type', '=', 'cash')],
    )
    date_from = fields.Date(
        string='Data Início',
        default=lambda self: date.today().replace(day=1),
    )
    date_to = fields.Date(
        string='Data Fim',
        default=lambda self: date.today(),
    )
    include_confirmed = fields.Boolean(
        string='Incluir Confirmados',
        default=True,
        help='Inclui movimentos já confirmados (reconciliados) na conta de caixa.',
    )

    # Campos para o ficheiro gerado
    file_data = fields.Binary(
        string='Ficheiro Excel',
        readonly=True,
    )
    file_name = fields.Char(
        string='Nome do Ficheiro',
        readonly=True,
    )
    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('done', 'Concluído'),
    ], default='draft')

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        """Atualiza o nome do ficheiro quando o diário muda."""
        if self.journal_id:
            self.file_name = f"caixa_{self.journal_id.code or 'export'}_{date.today().strftime('%Y%m%d')}.xlsx"

    def action_export(self):
        """Exporta os movimentos de caixa para Excel (Confirmados + Pendentes)."""
        self.ensure_one()

        if not OPENPYXL_INSTALLED:
            raise UserError(_('A biblioteca openpyxl não está instalada. Por favor instale com: pip install openpyxl'))

        if not self.journal_id:
            raise UserError(_('Por favor selecione um diário de caixa.'))

        # Buscar contas outstanding do diário (12402/12403)
        outstanding_accounts = (
            self.journal_id.inbound_payment_method_line_ids.mapped('payment_account_id') |
            self.journal_id.outbound_payment_method_line_ids.mapped('payment_account_id')
        )

        # Conta principal de caixa (11101 - onde o dinheiro "vive")
        cash_account = self.journal_id.default_account_id

        if not outstanding_accounts and not cash_account:
            raise UserError(_(
                'O diário "%s" não tem contas configuradas.\n'
                'Configure a conta de caixa e as contas nos métodos de pagamento.'
            ) % self.journal_id.name)

        # Domínio base para datas
        date_domain = [
            ('journal_id', '=', self.journal_id.id),
            ('parent_state', '=', 'posted'),
        ]
        if self.date_from:
            date_domain.append(('date', '>=', self.date_from))
        if self.date_to:
            date_domain.append(('date', '<=', self.date_to))

        # 1. MOVIMENTOS CONFIRMADOS (na conta de caixa principal - já estão no caixa)
        confirmed_lines = self.env['account.move.line']
        if self.include_confirmed and cash_account:
            confirmed_domain = date_domain + [
                ('account_id', '=', cash_account.id),
            ]
            confirmed_lines = self.env['account.move.line'].search(
                confirmed_domain,
                order='date asc, id asc'
            )

        # 2. MOVIMENTOS PENDENTES (nas contas outstanding 12402/12403, não reconciliados)
        pending_lines = self.env['account.move.line']
        if outstanding_accounts:
            pending_domain = date_domain + [
                ('account_id', 'in', outstanding_accounts.ids),
                ('reconciled', '=', False),
            ]
            pending_lines = self.env['account.move.line'].search(
                pending_domain,
                order='date asc, id asc'
            )

        if not confirmed_lines and not pending_lines:
            raise UserError(_('Não foram encontrados movimentos com os critérios especificados.'))

        # Gerar Excel
        excel_data = self._generate_excel(confirmed_lines, pending_lines)

        # Atualizar wizard
        self.write({
            'file_data': base64.b64encode(excel_data),
            'file_name': f"fecho_caixa_{self.journal_id.code or 'export'}_{date.today().strftime('%Y%m%d')}.xlsx",
            'state': 'done',
        })

        # Retornar a mesma view para download
        return {
            'name': _('Fecho de Caixa - Exportar'),
            'type': 'ir.actions.act_window',
            'res_model': 'cash.export.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
        }

    def _get_opening_balance(self):
        """Obtém o saldo inicial do caixa (último extracto ou cálculo).

        Filtra sempre pelo journal_id para funcionar correctamente mesmo
        quando a conta de caixa é partilhada entre vários diários.
        """
        # # Buscar último extracto do diário
        # last_statement = self.env['account.bank.statement'].search([
        #     ('journal_id', '=', self.journal_id.id),
        #     ('date', '<', self.date_from or date.today()),
        # ], order='date desc, id desc', limit=1)

        # if last_statement:
        #     return last_statement.balance_end_real

        # Se não há extracto, calcular saldo dos movimentos da CONTA até a data inicial
        # Filtra por account_id para capturar TODOS os movimentos (incluindo Operações Diversas)
        cash_account = self.journal_id.default_account_id
        if cash_account and self.date_from:
            domain = [
                ('account_id', '=', cash_account.id),
                ('parent_state', '=', 'posted'),
                ('date', '<', self.date_from),
            ]
            lines = self.env['account.move.line'].search(domain)
            return sum(line.debit - line.credit for line in lines)

        return 0.0

    def _generate_excel(self, confirmed_lines, pending_lines):
        """Gera o ficheiro Excel no formato de extracto bancário real.

        Uma única tabela com todos os movimentos, diferenciados por cor:
        - Verde: Confirmados (já no caixa)
        - Laranja: Pendentes (aguardam confirmação)
        """
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Extracto de Caixa'

        # Estilos
        header_font = Font(bold=True, color='FFFFFF')
        header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
        header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # Cores
        green_fill = PatternFill(start_color='C6EFCE', end_color='C6EFCE', fill_type='solid')  # Confirmados
        orange_fill = PatternFill(start_color='FFEB9C', end_color='FFEB9C', fill_type='solid')  # Pendentes
        total_fill = PatternFill(start_color='D9E1F2', end_color='D9E1F2', fill_type='solid')   # Totais
        balance_fill = PatternFill(start_color='E2EFDA', end_color='E2EFDA', fill_type='solid') # Saldo inicial

        # Cabeçalhos
        headers = [
            ('Data', 12),
            ('Referência', 18),
            ('Descrição', 35),
            ('Parceiro', 25),
            ('Entrada', 15),
            ('Saída', 15),
            ('Saldo', 15),
            ('Estado', 12),
            ('ID', 10),
        ]

        number_format = '#,##0.00'
        date_format = 'DD/MM/YYYY'
        current_row = 1

        # ==================== TÍTULO ====================
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=9)
        title_cell = ws.cell(row=current_row, column=1, value=f'EXTRACTO DE CAIXA - {self.journal_id.name}')
        title_cell.font = Font(bold=True, size=14)
        title_cell.alignment = Alignment(horizontal='center')
        current_row += 1

        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=9)
        date_cell = ws.cell(row=current_row, column=1, value=f'Período: {self.date_from.strftime("%d/%m/%Y") if self.date_from else "Início"} a {self.date_to.strftime("%d/%m/%Y") if self.date_to else "Fim"}')
        date_cell.alignment = Alignment(horizontal='center')
        current_row += 2

        # ==================== CABEÇALHOS DA TABELA ====================
        for col, (header, width) in enumerate(headers, 1):
            cell = ws.cell(row=current_row, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border
            ws.column_dimensions[get_column_letter(col)].width = width
        current_row += 1

        # ==================== SALDO INICIAL ====================
        opening_balance = self._get_opening_balance()
        running_balance = opening_balance

        for col in range(1, 10):
            ws.cell(row=current_row, column=col, value='').border = thin_border
        cell = ws.cell(row=current_row, column=3, value='SALDO INICIAL')
        cell.font = Font(bold=True)
        cell.fill = balance_fill
        cell.border = thin_border
        cell = ws.cell(row=current_row, column=7, value=opening_balance)
        cell.number_format = number_format
        cell.font = Font(bold=True)
        cell.fill = balance_fill
        cell.border = thin_border
        current_row += 1

        # ==================== MOVIMENTOS (ÚNICA TABELA) ====================
        # Combinar e ordenar por data
        all_movements = []

        for line in confirmed_lines:
            all_movements.append({
                'line': line,
                'date': line.date,
                'status': 'Confirmado',
                'fill': green_fill,
            })

        for line in pending_lines:
            all_movements.append({
                'line': line,
                'date': line.date,
                'status': 'Pendente',
                'fill': orange_fill,
            })

        # Ordenar por data e ID
        all_movements.sort(key=lambda x: (x['date'], x['line'].id))

        # Totais
        confirmed_total_entrada = 0.0
        confirmed_total_saida = 0.0
        pending_total_entrada = 0.0
        pending_total_saida = 0.0

        # Escrever movimentos
        for mov in all_movements:
            line = mov['line']
            entrada = line.debit
            saida = line.credit
            running_balance = running_balance + entrada - saida

            if mov['status'] == 'Confirmado':
                confirmed_total_entrada += entrada
                confirmed_total_saida += saida
            else:
                pending_total_entrada += entrada
                pending_total_saida += saida

            self._write_line_row_v2(ws, current_row, line, entrada, saida, running_balance,
                                    mov['fill'], thin_border, number_format, date_format, mov['status'])
            current_row += 1

        # ==================== SALDO FINAL ====================
        current_row += 1
        for col in range(1, 10):
            ws.cell(row=current_row, column=col, value='').border = thin_border
        cell = ws.cell(row=current_row, column=3, value='SALDO FINAL')
        cell.font = Font(bold=True)
        cell.fill = total_fill
        cell.border = thin_border
        cell = ws.cell(row=current_row, column=7, value=running_balance)
        cell.number_format = number_format
        cell.font = Font(bold=True)
        cell.fill = total_fill
        cell.border = thin_border
        current_row += 2

        # ==================== RESUMO ====================
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=9)
        summary_cell = ws.cell(row=current_row, column=1, value='RESUMO DO FECHO DE CAIXA')
        summary_cell.font = Font(bold=True, color='FFFFFF')
        summary_cell.fill = header_fill
        summary_cell.alignment = Alignment(horizontal='center')
        current_row += 1

        # Saldo Inicial
        ws.cell(row=current_row, column=1, value='Saldo Inicial:').font = Font(bold=True)
        cell = ws.cell(row=current_row, column=3, value=opening_balance)
        cell.number_format = number_format
        cell.fill = balance_fill
        cell.border = thin_border
        current_row += 1

        # Confirmados
        balance_after_confirmed = opening_balance + confirmed_total_entrada - confirmed_total_saida

        ws.cell(row=current_row, column=1, value='(+) Entradas Confirmadas:').font = Font(bold=True)
        cell = ws.cell(row=current_row, column=3, value=confirmed_total_entrada)
        cell.number_format = number_format
        cell.fill = green_fill
        cell.border = thin_border
        ws.cell(row=current_row, column=4, value=f'({len(confirmed_lines)} mov.)')
        current_row += 1

        ws.cell(row=current_row, column=1, value='(-) Saídas Confirmadas:').font = Font(bold=True)
        cell = ws.cell(row=current_row, column=3, value=confirmed_total_saida)
        cell.number_format = number_format
        cell.fill = green_fill
        cell.border = thin_border
        current_row += 1

        ws.cell(row=current_row, column=1, value='= Saldo Confirmado:').font = Font(bold=True)
        cell = ws.cell(row=current_row, column=3, value=balance_after_confirmed)
        cell.number_format = number_format
        cell.font = Font(bold=True)
        cell.fill = green_fill
        cell.border = thin_border
        current_row += 1

        # Pendentes
        ws.cell(row=current_row, column=1, value='(+) Entradas Pendentes:').font = Font(bold=True)
        cell = ws.cell(row=current_row, column=3, value=pending_total_entrada)
        cell.number_format = number_format
        cell.fill = orange_fill
        cell.border = thin_border
        ws.cell(row=current_row, column=4, value=f'({len(pending_lines)} mov.)')
        current_row += 1

        ws.cell(row=current_row, column=1, value='(-) Saídas Pendentes:').font = Font(bold=True)
        cell = ws.cell(row=current_row, column=3, value=pending_total_saida)
        cell.number_format = number_format
        cell.fill = orange_fill
        cell.border = thin_border
        current_row += 1

        # Saldo Final
        ws.cell(row=current_row, column=1, value='= SALDO FINAL ESPERADO:').font = Font(bold=True, size=12)
        cell = ws.cell(row=current_row, column=3, value=running_balance)
        cell.number_format = number_format
        cell.font = Font(bold=True, size=12)
        cell.fill = total_fill
        cell.border = thin_border
        current_row += 2

        # Legenda
        ws.cell(row=current_row, column=1, value='Legenda:')
        current_row += 1
        cell = ws.cell(row=current_row, column=1, value='  ■ Confirmado')
        cell.fill = green_fill
        ws.cell(row=current_row, column=2, value='= Movimento já no caixa')
        current_row += 1
        cell = ws.cell(row=current_row, column=1, value='  ■ Pendente')
        cell.fill = orange_fill
        ws.cell(row=current_row, column=2, value='= Aguarda confirmação')
        current_row += 2

        # Data exportação
        ws.cell(row=current_row, column=1, value=f'Exportado em: {date.today().strftime("%d/%m/%Y")}')

        # Salvar
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        return output.read()

    def _write_line_row_v2(self, ws, row, line, entrada, saida, saldo, fill, border, number_format, date_format, status):
        """Escreve uma linha de movimento no formato de extracto bancário."""
        # Data
        cell = ws.cell(row=row, column=1, value=line.date)
        cell.number_format = date_format
        cell.fill = fill
        cell.border = border

        # Referência
        cell = ws.cell(row=row, column=2, value=line.ref or '')
        cell.fill = fill
        cell.border = border

        # Descrição
        cell = ws.cell(row=row, column=3, value=line.name or '')
        cell.fill = fill
        cell.border = border

        # Parceiro
        cell = ws.cell(row=row, column=4, value=line.partner_id.name if line.partner_id else '')
        cell.fill = fill
        cell.border = border

        # Entrada (Débito Odoo = dinheiro entra)
        cell = ws.cell(row=row, column=5, value=entrada if entrada else '')
        if entrada:
            cell.number_format = number_format
        cell.fill = fill
        cell.border = border

        # Saída (Crédito Odoo = dinheiro sai)
        cell = ws.cell(row=row, column=6, value=saida if saida else '')
        if saida:
            cell.number_format = number_format
        cell.fill = fill
        cell.border = border

        # Saldo (acumulado)
        cell = ws.cell(row=row, column=7, value=saldo)
        cell.number_format = number_format
        cell.fill = fill
        cell.border = border

        # Estado
        cell = ws.cell(row=row, column=8, value=status)
        cell.alignment = Alignment(horizontal='center')
        cell.fill = fill
        cell.border = border

        # ID
        cell = ws.cell(row=row, column=9, value=line.id)
        cell.fill = fill
        cell.border = border

    def action_download(self):
        """Retorna a ação para download do ficheiro."""
        self.ensure_one()

        if not self.file_data:
            raise UserError(_('Nenhum ficheiro disponível para download.'))

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model=cash.export.wizard&id={self.id}&field=file_data&filename_field=file_name&download=true',
            'target': 'self',
        }
