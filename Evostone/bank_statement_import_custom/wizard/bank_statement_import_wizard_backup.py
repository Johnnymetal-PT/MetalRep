from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import logging
import tempfile
import os
import io
try:
    import openpyxl
except ImportError:
    openpyxl = None
from ..models.bim_parser import BIMStatementParser

_logger = logging.getLogger(__name__)


class BankStatementImportWizard(models.TransientModel):
    _name = 'bank.statement.import.wizard'
    _description = 'Bank Statement Import Wizard'

    # Campo de seleção de banco
    bank_type = fields.Selection([
        ('bim', 'BIM - Banco Internacional de Moçambique'),
        ('bci', 'BCI - Banco Comercial e de Investimentos'),
        ('card', 'CARD - Extratos de Cartão (Débito/Crédito/Pré-pago)'),
    ], string='Selecione o Banco', required=True)
    
    # Campo de upload de arquivo
    data_file = fields.Binary(
        string='Arquivo do Extrato',
        help='Selecione o arquivo do extrato bancário (CSV, XLS, XLSX)'
    )
    file_name = fields.Char(string='Nome do Arquivo')
    
    # Campo de mensagem informativa
    message = fields.Text(
        string='Informações',
        readonly=True,
        default='Por favor, selecione o banco e faça upload do arquivo do extrato.'
    )
    
    @api.onchange('bank_type')
    def _onchange_bank_type(self):
        """Atualiza mensagem quando banco é selecionado"""
        if self.bank_type:
            bank_name = dict(self._fields['bank_type'].selection).get(self.bank_type)
            self.message = f"Banco selecionado: {bank_name}\n\nAgora faça upload do arquivo do extrato."
    
    @api.onchange('data_file', 'file_name')
    def _onchange_data_file(self):
        """Atualiza mensagem quando arquivo é carregado"""
        if self.data_file and self.file_name:
            if self.bank_type:
                bank_name = dict(self._fields['bank_type'].selection).get(self.bank_type)
                self.message = f"Banco: {bank_name}\nArquivo: {self.file_name}\n\nPronto para importar!"
            else:
                self.message = f"Arquivo: {self.file_name}\n\nPor favor, selecione o banco."
    
    def action_import(self):
        """Processa a importação"""
        self.ensure_one()
        
        if not self.bank_type:
            raise UserError('Por favor, selecione o banco.')
        
        if not self.data_file:
            raise UserError('Por favor, selecione um arquivo para importar.')
        
        # Log da importação
        bank_name = dict(self._fields['bank_type'].selection).get(self.bank_type)
        _logger.info(f"Importando extrato do {bank_name}: {self.file_name}")
        
        try:
            # Process file based on bank type
            if self.bank_type == 'bim':
                _logger.info("Wizard: Processing BIM file")
                _logger.info(f"Wizard: File name = {self.file_name}")
                _logger.info(f"Wizard: Data file size = {len(self.data_file) if self.data_file else 0}")
                
                # Use BIM parser to format the file
                _logger.info("Wizard: Creating BIMStatementParser instance")
                parser = BIMStatementParser()
                _logger.info("Wizard: Parser created successfully, calling parse_file")
                formatted_data = parser.parse_file(self.data_file, self.file_name, "bim")
                _logger.info(f"Wizard: parse_file returned, formatted_data = {formatted_data is not None}")
                
                _logger.info(f"BIM file processed: {formatted_data.get('transaction_count')} transactions found")
                
                # Save formatted file temporarily  
                temp_dir = tempfile.gettempdir()
                temp_file_path = os.path.join(temp_dir, formatted_data['file_name'])
                
                with open(temp_file_path, 'wb') as f:
                    f.write(base64.b64decode(formatted_data['file']))
                
                _logger.info(f"Formatted file saved to: {temp_file_path}")
                
                # Create attachment with formatted file
                attachment = self.env['ir.attachment'].create({
                    'name': formatted_data['file_name'],
                    'type': 'binary',
                    'datas': formatted_data['file'],
                    'res_model': 'account.bank.statement.line',
                    'res_id': False,
                })
                
                # Get journal from context or find default
                journal_id = self.env.context.get('journal_id')
                if not journal_id:
                    bank_journal = self.env['account.journal'].search([
                        ('type', '=', 'bank'),
                        ('company_id', '=', self.env.company.id)
                    ], limit=1)
                    if bank_journal:
                        journal_id = bank_journal.id
                
                # Create bank statement lines directly from parsed data
                _logger.info(f"Creating {formatted_data.get('transaction_count')} bank statement lines")
                
                # Decode the XLSX to get the transactions
                xlsx_data = base64.b64decode(formatted_data['file'])
                wb = openpyxl.load_workbook(io.BytesIO(xlsx_data))
                sheet = wb.active
                
                created_lines = []
                # Skip header row
                for row in sheet.iter_rows(min_row=2, values_only=True):
                    if row and row[0]:  # If date exists
                        line_vals = {
                            'date': row[0],  # Date
                            'payment_ref': row[1] or '',  # Label
                            'amount': float(row[2]) if row[2] else 0.0,  # Amount
                        }
                        
                        # Add journal_id if available
                        if journal_id:
                            line_vals['journal_id'] = journal_id
                        
                        # Create the bank statement line
                        try:
                            line = self.env['account.bank.statement.line'].create(line_vals)
                            created_lines.append(line.id)
                            _logger.info(f"Created line: {line_vals['date']} - {line_vals['amount']}")
                        except Exception as e:
                            _logger.error(f"Error creating line: {e}")
                            raise UserError(f"Erro ao criar linha: {e}")
                
                _logger.info(f"Successfully created {len(created_lines)} bank statement lines")
                
                # Redirect to accounting dashboard
                _logger.info(f"Successfully imported {len(created_lines)} transactions, redirecting to /odoo/accounting")
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/odoo/accounting',
                    'target': 'self',
                }
                
            elif self.bank_type == 'bci':
                _logger.info("Wizard: Processing BCI file")
                _logger.info(f"Wizard: File name = {self.file_name}")
                _logger.info(f"Wizard: Data file size = {len(self.data_file) if self.data_file else 0}")
                
                # Use BIM parser for BCI format (it handles both)
                _logger.info("Wizard: Creating BIMStatementParser instance for BCI")
                parser = BIMStatementParser()
                _logger.info("Wizard: Parser created successfully, calling parse_file for BCI")
                formatted_data = parser.parse_file(self.data_file, self.file_name, "bci")
                _logger.info(f"Wizard: parse_file returned for BCI, formatted_data = {formatted_data is not None}")
                
                _logger.info(f"BCI file processed: {formatted_data.get('transaction_count')} transactions found")
                
                # Get journal from context or find default
                journal_id = self.env.context.get('journal_id')
                if not journal_id:
                    bank_journal = self.env['account.journal'].search([
                        ('type', '=', 'bank'),
                        ('company_id', '=', self.env.company.id)
                    ], limit=1)
                    if bank_journal:
                        journal_id = bank_journal.id
                
                # Create bank statement lines directly from parsed data
                _logger.info(f"Creating {formatted_data.get('transaction_count')} bank statement lines for BCI")
                
                # Decode the XLSX to get the transactions
                xlsx_data = base64.b64decode(formatted_data['file'])
                wb = openpyxl.load_workbook(io.BytesIO(xlsx_data))
                sheet = wb.active
                
                created_lines = []
                # Skip header row
                for row in sheet.iter_rows(min_row=2, values_only=True):
                    if row and row[0]:  # If date exists
                        line_vals = {
                            'date': row[0],  # Date
                            'payment_ref': row[1] or '',  # Label
                            'amount': float(row[2]) if row[2] else 0.0,  # Amount
                        }
                        
                        # Add journal_id if available
                        if journal_id:
                            line_vals['journal_id'] = journal_id
                        
                        # Create the bank statement line
                        try:
                            line = self.env['account.bank.statement.line'].create(line_vals)
                            created_lines.append(line.id)
                            _logger.info(f"Created BCI line: {line_vals['date']} - {line_vals['amount']}")
                        except Exception as e:
                            _logger.error(f"Error creating BCI line: {e}")
                            raise UserError(f"Erro ao criar linha BCI: {e}")
                
                _logger.info(f"Successfully created {len(created_lines)} BCI bank statement lines")
                
                # Redirect to accounting dashboard
                _logger.info(f"Successfully imported {len(created_lines)} BCI transactions, redirecting to /odoo/accounting")
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/odoo/accounting',
                    'target': 'self',
                }
                
            elif self.bank_type == 'card':
                _logger.info("Wizard: Processing CARD file")
                _logger.info(f"Wizard: File name = {self.file_name}")
                _logger.info(f"Wizard: Data file size = {len(self.data_file) if self.data_file else 0}")
                
                # Use BIM parser for CARD format
                _logger.info("Wizard: Creating BIMStatementParser instance for CARD")
                parser = BIMStatementParser()
                _logger.info("Wizard: Parser created successfully, calling parse_file for CARD")
                formatted_data = parser.parse_file(self.data_file, self.file_name, "card")
                _logger.info(f"Wizard: parse_file returned for CARD, formatted_data = {formatted_data is not None}")
                
                _logger.info(f"CARD file processed: {formatted_data.get('transaction_count')} transactions found")
                
                # Get journal from context or find default
                journal_id = self.env.context.get('journal_id')
                if not journal_id:
                    bank_journal = self.env['account.journal'].search([
                        ('type', '=', 'bank'),
                        ('company_id', '=', self.env.company.id)
                    ], limit=1)
                    if bank_journal:
                        journal_id = bank_journal.id
                
                # Create bank statement lines directly from parsed data
                _logger.info(f"Creating {formatted_data.get('transaction_count')} bank statement lines for CARD")
                
                # Decode the XLSX to get the transactions
                xlsx_data = base64.b64decode(formatted_data['file'])
                wb = openpyxl.load_workbook(io.BytesIO(xlsx_data))
                sheet = wb.active
                
                created_lines = []
                # Skip header row
                for row in sheet.iter_rows(min_row=2, values_only=True):
                    if row and row[0]:  # If date exists
                        line_vals = {
                            'date': row[0],  # Date
                            'payment_ref': row[1] or '',  # Label
                            'amount': float(row[2]) if row[2] else 0.0,  # Amount
                        }
                        
                        # Add journal_id if available
                        if journal_id:
                            line_vals['journal_id'] = journal_id
                        
                        # Create the bank statement line
                        try:
                            line = self.env['account.bank.statement.line'].create(line_vals)
                            created_lines.append(line.id)
                            _logger.info(f"Created CARD line: {line_vals['date']} - {line_vals['amount']}")
                        except Exception as e:
                            _logger.error(f"Error creating CARD line: {e}")
                            raise UserError(f"Erro ao criar linha CARD: {e}")
                
                _logger.info(f"Successfully created {len(created_lines)} CARD bank statement lines")
                
                # Redirect to accounting dashboard
                _logger.info(f"Successfully imported {len(created_lines)} CARD transactions, redirecting to /odoo/accounting")
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/odoo/accounting',
                    'target': 'self',
                }
            else:
                # For other banks, use standard import
                raise UserError('Banco não suportado.')
                
        except Exception as e:
            _logger.error(f"Error during import: {str(e)}")
            raise UserError(f'Erro durante importação: {str(e)}')
    
    def action_cancel(self):
        """Cancela o wizard"""
        return {'type': 'ir.actions.act_window_close'}