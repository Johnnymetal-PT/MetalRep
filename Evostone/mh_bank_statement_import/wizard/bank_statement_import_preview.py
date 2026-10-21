# -*- coding: utf-8 -*-
import base64
import json
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BankStatementImportPreview(models.TransientModel):
    _name = 'mh.bank.statement.import.preview'
    _description = 'Preview de Importação de Extracto Bancário'

    journal_id = fields.Many2one('account.journal', string='Diário', required=True)
    attachment_id = fields.Many2one('ir.attachment', string='Ficheiro')
    filename = fields.Char(string='Nome do Ficheiro')

    # Informações do extracto
    bank_name = fields.Char(string='Banco', readonly=True)
    account_number = fields.Char(string='Número da Conta', readonly=True)
    currency_code = fields.Char(string='Moeda', readonly=True)
    statement_name = fields.Char(string='Nome do Extracto')
    statement_date = fields.Date(string='Data do Extracto')
    balance_start = fields.Float(string='Saldo Inicial', digits=(16, 2))
    balance_end = fields.Float(string='Saldo Final', digits=(16, 2))
    total_transactions = fields.Integer(string='Total de Transações', readonly=True)
    total_credit = fields.Float(string='Total Créditos', readonly=True, digits=(16, 2))
    total_debit = fields.Float(string='Total Débitos', readonly=True, digits=(16, 2))

    # Linhas de preview
    line_ids = fields.One2many('mh.bank.statement.import.preview.line', 'preview_id', string='Transações')

    # Dados JSON para importação
    import_data = fields.Text(string='Dados de Importação')

    def action_import(self):
        """Confirma a importação do extracto usando dados do wizard"""
        self.ensure_one()

        if not self.line_ids:
            raise UserError(_("Não há transações para importar."))

        journal = self.journal_id

        # Verificar se o journal tem conta padrão
        if not journal.default_account_id:
            raise UserError(_('Deve definir uma Conta Padrão para o diário: %s', journal.name))

        # BIM: o banco constrói o saldo pela DATA VALOR. Para o extracto bater
        # linha-a-linha com o banco (ex.: POS com Data Valor posterior à
        # Data Transação), usamos a Data Valor como data da linha no BIM.
        # Outros bancos mantêm a Data Transação.
        use_value_date = (self.bank_name or '').strip().upper() == 'BIM'

        # Preparar linhas do extracto a partir do wizard
        line_vals = []
        for line in self.line_ids:
            line_date = (line.date_valor or line.date) if use_value_date else line.date

            # Gerar unique_import_id
            unique_id = f"{self.bank_name}-{self.account_number}-{line_date}-{line.sequence}-{abs(line.amount):.2f}"

            line_vals.append({
                'date': line_date,
                'payment_ref': line.payment_ref or 'Sem descrição',
                'amount': line.amount,
                'journal_id': journal.id,
                'unique_import_id': unique_id,
            })

        # Criar o bank statement
        statement = self.env['account.bank.statement'].create({
            'name': self.statement_name,
            'date': self.statement_date,
            'balance_start': self.balance_start,
            'balance_end_real': self.balance_end,
            'journal_id': journal.id,
            'line_ids': [(0, 0, vals) for vals in line_vals],
        })

        # Actualizar fonte do journal
        if journal.bank_statements_source != 'file_import':
            journal.sudo().bank_statements_source = 'file_import'

        # Abrir widget de reconciliação
        if statement.line_ids:
            return self.env['account.bank.statement.line']._action_open_bank_reconciliation_widget(
                extra_domain=[('statement_id', '=', statement.id)],
                default_context={
                    'search_default_not_matched': True,
                    'default_journal_id': journal.id,
                },
            )

        # Se criou o statement, mostrar
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.bank.statement',
            'view_mode': 'form',
            'res_id': statement.id,
            'target': 'current',
        }

    def action_cancel(self):
        """Cancela a importação"""
        return {'type': 'ir.actions.act_window_close'}


class BankStatementImportPreviewLine(models.TransientModel):
    _name = 'mh.bank.statement.import.preview.line'
    _description = 'Linha de Preview de Importação'
    _order = 'sequence, date'

    preview_id = fields.Many2one('mh.bank.statement.import.preview', string='Preview', ondelete='cascade')
    sequence = fields.Integer(string='Seq.')

    # Campos comuns BIM e BCI
    date = fields.Date(string='Data Transação')
    date_valor = fields.Date(string='Data Valor')
    payment_ref = fields.Char(string='Descrição')
    debit = fields.Float(string='Débito', digits=(16, 2))
    credit = fields.Float(string='Crédito', digits=(16, 2))
    balance = fields.Float(string='Saldo', digits=(16, 2))

    # Campos específicos BCI
    num_doc = fields.Char(string='Nº Documento')
    num_oper = fields.Char(string='Nº Operação')
    currency = fields.Char(string='Moeda')

    # Campo amount para importação (calculado)
    amount = fields.Float(string='Valor', digits=(16, 2))

    # Campos auxiliares
    partner_name = fields.Char(string='Parceiro')
    ref = fields.Char(string='Referência')
    note = fields.Text(string='Notas')
