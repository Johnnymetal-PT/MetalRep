import base64
import io
import logging
from datetime import datetime
import csv
from odoo.exceptions import UserError

# Test if libraries are available with more robust import
HAS_EXCEL_LIBS = False
import_error = None

try:
    import openpyxl
    HAS_EXCEL_LIBS = True
except ImportError as e:
    import_error = str(e)
    # Try alternative import
    try:
        import sys
        import importlib
        openpyxl = importlib.import_module('openpyxl')
        HAS_EXCEL_LIBS = True
        import_error = None
    except Exception as e2:
        import_error = f"Primary: {e}, Alternative: {e2}"

# Try to import xlrd as well (optional for xls support)
try:
    import xlrd
except ImportError:
    xlrd = None  # xlrd is optional, we can work with just openpyxl

_logger = logging.getLogger(__name__)

# Log library availability at module load
if HAS_EXCEL_LIBS:
    _logger.info("BIM Parser: openpyxl loaded successfully")
    if xlrd:
        _logger.info("BIM Parser: xlrd also loaded successfully")
    else:
        _logger.info("BIM Parser: xlrd not available (optional)")
else:
    _logger.error(f"BIM Parser: Failed to import Excel libraries: {import_error}")


class BIMStatementParser:
    """Parser for BIM (Millennium BIM) bank statements and Card statements"""
    
    def __init__(self):
        _logger.info("BIM Parser: Initializing BIMStatementParser")
        self.header_lines_to_skip = 11
        self.bim_info = {}  # Para armazenar informações do extrato BIM
        _logger.info(f"BIM Parser: HAS_EXCEL_LIBS = {HAS_EXCEL_LIBS}")
        if not HAS_EXCEL_LIBS:
            _logger.error(f"BIM Parser: Excel libraries not available: {import_error}")
            raise UserError(f"Excel libraries not available: {import_error}")
        _logger.info("BIM Parser: Initialization complete")
        
    def parse_file(self, file_content, file_name, bank_type="bim"):
        """
        Parse bank statement file and return formatted data for Odoo import
        Supports BIM, BCI, and CARD formats
        """
        try:
            _logger.info(f"BIM Parser: Starting to parse file {file_name}")
            
            # Decode file content
            file_data = base64.b64decode(file_content)
            _logger.info(f"BIM Parser: File decoded, size: {len(file_data)} bytes")
            
            # Determine parsing method based on bank type and file extension
            if bank_type.lower() == "card":
                # Card statements have different format
                if file_name.lower().endswith('.csv'):
                    _logger.info("BIM Parser: Processing CARD CSV file")
                    return self._parse_card_csv(file_data)
                elif file_name.lower().endswith('.xls'):
                    _logger.info("BIM Parser: Processing CARD XLS file") 
                    return self._parse_card_xls(file_data)
                elif file_name.lower().endswith('.xlsx'):
                    _logger.info("BIM Parser: Processing CARD XLSX file")
                    return self._parse_card_xls(file_data)  # Same as XLS processing
                else:
                    raise UserError("Formato de arquivo de cartão não suportado. Use CSV, XLS ou XLSX.")
            else:
                # BIM/BCI format
                if file_name.lower().endswith('.xlsx'):
                    _logger.info("BIM Parser: Processing as XLSX file")
                    result = self._parse_xlsx(file_data)
                    _logger.info(f"BIM Parser: XLSX parsing complete, got result: {result is not None}")
                    return result
                elif file_name.lower().endswith('.xls'):
                    _logger.info("BIM Parser: Processing as XLS file")
                    return self._parse_xls(file_data)
                elif file_name.lower().endswith('.csv'):
                    _logger.info("BIM Parser: Processing as CSV file")
                    return self._parse_csv(file_data)
                else:
                    raise UserError("Formato de arquivo não suportado. Use XLSX, XLS ou CSV.")
                
        except Exception as e:
            _logger.error(f"Erro ao processar arquivo BIM: {str(e)}")
            import traceback
            _logger.error(traceback.format_exc())
            raise UserError(f"Erro ao processar arquivo: {str(e)}")
    
    def _extract_bim_header_info(self, sheet):
        """Extrai informações do cabeçalho do extrato BIM"""
        info = {}
        
        try:
            # Período (linha 6, coluna 3)
            periodo_cell = sheet.cell(row=6, column=3).value
            if periodo_cell and 'de' in str(periodo_cell) and 'até' in str(periodo_cell):
                import re
                dates = re.findall(r'\d{2}-\d{2}-\d{4}', str(periodo_cell))
                if len(dates) == 2:
                    info['period_start'] = dates[0]
                    info['period_end'] = dates[1]
            
            # Saldo inicial (linha 7, coluna 9 ou procurar nas colunas 5-9)
            for col in [9, 8, 7, 6, 5]:
                val = sheet.cell(row=7, column=col).value
                if val:
                    info['initial_balance'] = val
                    break
            
            # Total créditos (linha 8, coluna 9)
            for col in [9, 8, 7, 6, 5]:
                val = sheet.cell(row=8, column=col).value
                if val:
                    info['total_credits'] = val
                    break
            
            # Total débitos (linha 9, coluna 9)
            for col in [9, 8, 7, 6, 5]:
                val = sheet.cell(row=9, column=col).value
                if val:
                    info['total_debits'] = val
                    break
            
            # Saldo final (linha 10, coluna 9)
            for col in [9, 8, 7, 6, 5]:
                val = sheet.cell(row=10, column=col).value
                if val:
                    info['final_balance'] = val
                    break
            
            # Primeira transação (linha 12)
            first_row = list(sheet.iter_rows(min_row=12, max_row=12, values_only=True))[0]
            if first_row and first_row[2]:  # Coluna 3 tem a data
                info['first_transaction'] = {
                    'date': first_row[2],
                    'description': first_row[4] if len(first_row) > 4 else '',
                    'debit': first_row[6] if len(first_row) > 6 else None,
                    'credit': first_row[7] if len(first_row) > 7 else None,
                    'balance': first_row[9] if len(first_row) > 9 else None
                }
            
            # Última transação - procura de trás para frente
            last_row_num = None
            for row_num in range(sheet.max_row, 11, -1):
                date_cell = sheet.cell(row=row_num, column=3).value
                if date_cell:
                    last_row_num = row_num
                    break
            
            if last_row_num:
                last_row = list(sheet.iter_rows(min_row=last_row_num, max_row=last_row_num, values_only=True))[0]
                if last_row:
                    info['last_transaction'] = {
                        'date': last_row[2] if len(last_row) > 2 else None,
                        'description': last_row[4] if len(last_row) > 4 else '',
                        'debit': last_row[6] if len(last_row) > 6 else None,
                        'credit': last_row[7] if len(last_row) > 7 else None,
                        'balance': last_row[9] if len(last_row) > 9 else None
                    }
                    info['last_row_num'] = last_row_num
            
            _logger.info(f"BIM Header Info extracted: {info}")
            
        except Exception as e:
            _logger.error(f"Erro ao extrair informações do cabeçalho BIM: {e}")
        
        return info
    
    def _extract_bci_header_info(self, sheet):
        """Extract header information from BCI statement (XLS format)"""
        info = {}
        try:
            _logger.info("Extracting BCI header information")
            
            # BCI format structure (based on real file):
            # Row 2 (index 1): "Conta" in col A, account number in col B
            # Row 3 (index 2): "Nib" in col A, NIB in col B
            # Row 4 (index 3): "Saldo Anterior" in col A, balance in col B
            # Row 6 (index 5): "Saldo Disponível" in col A, balance in col B
            # Row 7 (index 6): "Saldo Contabilístico" in col A, balance in col B
            
            # Extract account number (row 2, column B)
            if sheet.nrows > 1:
                cell_a = sheet.cell(1, 0).value if sheet.ncols > 0 else None
                cell_b = sheet.cell(1, 1).value if sheet.ncols > 1 else None
                
                if cell_a and isinstance(cell_a, str) and 'conta' in cell_a.lower():
                    if cell_b:
                        # Handle if it's a float (Excel sometimes stores numbers as floats)
                        if isinstance(cell_b, float):
                            info['account_number'] = str(int(cell_b))
                        else:
                            info['account_number'] = str(cell_b).strip()
                        _logger.info(f"Found BCI account: {info['account_number']}")
            
            # Extract available balance (row 6, column B)
            if sheet.nrows > 5:
                cell_a = sheet.cell(5, 0).value if sheet.ncols > 0 else None
                cell_b = sheet.cell(5, 1).value if sheet.ncols > 1 else None
                
                if cell_a and isinstance(cell_a, str) and ('saldo disponível' in cell_a.lower() or 'saldo disponivel' in cell_a.lower()):
                    if cell_b:
                        info['available_balance'] = str(cell_b).strip()
                        _logger.info(f"Found BCI available balance: {info['available_balance']}")
            
            # Extract accounting balance (row 7, column B)
            if sheet.nrows > 6:
                cell_a = sheet.cell(6, 0).value if sheet.ncols > 0 else None
                cell_b = sheet.cell(6, 1).value if sheet.ncols > 1 else None
                
                if cell_a and isinstance(cell_a, str) and ('saldo contabilístico' in cell_a.lower() or 'saldo contabilistico' in cell_a.lower()):
                    if cell_b:
                        info['accounting_balance'] = str(cell_b).strip()
                        _logger.info(f"Found BCI accounting balance: {info['accounting_balance']}")
            
            # Extract NIB (row 3, column B) - optional
            if sheet.nrows > 2:
                cell_a = sheet.cell(2, 0).value if sheet.ncols > 0 else None
                cell_b = sheet.cell(2, 1).value if sheet.ncols > 1 else None
                
                if cell_a and isinstance(cell_a, str) and 'nib' in cell_a.lower():
                    if cell_b:
                        info['nib'] = str(cell_b).strip()
                        _logger.info(f"Found BCI NIB: {info['nib']}")
            
            # Extract previous balance (row 4, column B) - optional
            if sheet.nrows > 3:
                cell_a = sheet.cell(3, 0).value if sheet.ncols > 0 else None
                cell_b = sheet.cell(3, 1).value if sheet.ncols > 1 else None
                
                if cell_a and isinstance(cell_a, str) and 'saldo anterior' in cell_a.lower():
                    if cell_b:
                        info['previous_balance'] = str(cell_b).strip()
                        _logger.info(f"Found BCI previous balance: {info['previous_balance']}")
            
            # Extract period dates from transactions if available
            # First transaction date and last transaction date will be extracted later
            
            _logger.info(f"BCI header info extracted: {info}")
            
        except Exception as e:
            _logger.warning(f"Error extracting BCI header info: {str(e)}")
        
        return info
    
    def _parse_xlsx(self, file_data):
        """Parse XLSX file format"""
        try:
            _logger.info("BIM Parser: _parse_xlsx called")
            # Create a BytesIO object from file data
            file_stream = io.BytesIO(file_data)
            
            # Load workbook
            wb = openpyxl.load_workbook(file_stream, data_only=True)
            sheet = wb.active
            
            _logger.info(f"BIM Parser: Sheet '{sheet.title}' with {sheet.max_row} rows")
            
            # Extrai informações do cabeçalho BIM
            self.bim_info = self._extract_bim_header_info(sheet)
            
            transactions = []
            
            # Process transactions starting from row 12
            row_count = 0
            for row_idx, row in enumerate(sheet.iter_rows(min_row=12, values_only=True), start=12):
                row_count += 1
                # Skip completely empty rows
                if not row or all(v is None for v in row):
                    continue
                    
                transaction = self._process_row(row, row_idx)
                if transaction:
                    transactions.append(transaction)
                    _logger.info(f"BIM Parser: Transaction added from row {row_idx}: {transaction}")
            
            _logger.info(f"BIM Parser: Processed {row_count} rows, found {len(transactions)} transactions")
            
            if not transactions:
                _logger.warning("BIM Parser: No transactions found!")
                # Log some sample rows for debugging
                for i, row in enumerate(sheet.iter_rows(min_row=12, max_row=15, values_only=True), start=12):
                    _logger.warning(f"  Sample row {i}: {row[:10] if row else 'Empty'}")
            
            result = self._format_for_odoo_import(transactions, "bim")
            # Adiciona informações do cabeçalho BIM ao resultado
            result['bim_info'] = self.bim_info
            _logger.info(f"BIM Parser: Formatted result with {result.get('transaction_count')} transactions")
            return result
            
        except Exception as e:
            _logger.error(f"Erro ao processar XLSX: {str(e)}")
            import traceback
            _logger.error(traceback.format_exc())
            raise UserError(f"Erro ao processar arquivo XLSX: {str(e)}")
    
    def _process_row(self, row, row_number):
        """Process a single row from BIM statement"""
        try:
            _logger.debug(f"Processing row {row_number}")
            
            # Auto-detect format based on where data starts
            # Check if first columns are None/empty (real file format)
            if len(row) > 2 and row[0] is None and row[1] is None and row[2] is not None:
                # Format 2: Real file (data starts at index 2/column C)
                transaction_date = row[2] if len(row) > 2 else None
                value_date = row[3] if len(row) > 3 else None
                description = row[4] if len(row) > 4 else ""
                # Skip column F (index 5) - it's None
                debit = row[6] if len(row) > 6 else 0
                # Skip column H (index 7) - it's None
                credit = row[8] if len(row) > 8 else 0
                balance = row[9] if len(row) > 9 else 0
                _logger.debug(f"Row {row_number}: Real format - date={transaction_date}, debit={debit}, credit={credit}")
            else:
                # Format 1: Test file (data starts at index 0/column A)
                transaction_date = row[0] if len(row) > 0 else None
                value_date = row[1] if len(row) > 1 else None
                description = row[2] if len(row) > 2 else ""
                debit = row[3] if len(row) > 3 else 0
                credit = row[4] if len(row) > 4 else 0
                balance = row[5] if len(row) > 5 else 0
                _logger.debug(f"Row {row_number}: Test format - date={transaction_date}, debit={debit}, credit={credit}")
            
            # Skip if no date
            if not transaction_date:
                return None
            
            # Skip header row if it contains text like "Data" 
            if isinstance(transaction_date, str) and 'data' in transaction_date.lower():
                return None
            
            # Parse date (handle different formats)
            date_obj = self._parse_date(transaction_date)
            if not date_obj:
                _logger.debug(f"Could not parse date in row {row_number}: {transaction_date}")
                return None
            
            # Calculate amount
            # Note: In real files, debits come as negative values already
            # In test files, debits come as positive values
            amount = 0.0
            
            # Process debit
            if debit and debit != 0:
                debit_parsed = self._parse_amount(debit)
                # If debit is already negative (real file), use as is
                # If debit is positive (test file), make it negative
                if debit_parsed < 0:
                    amount = debit_parsed  # Already negative
                else:
                    amount = -debit_parsed  # Make it negative
            
            # Process credit (always positive when present)
            if credit and credit != 0:
                credit_parsed = self._parse_amount(credit)
                if credit_parsed != 0:
                    amount = abs(credit_parsed)  # Ensure positive
            
            # Skip if amount is zero
            if amount == 0:
                return None
            
            transaction = {
                'date': date_obj,
                'payment_ref': str(description).strip() if description else "",
                'amount': amount,
                'balance': self._parse_amount(balance) if balance else 0,
                'row_number': row_number
            }
            
            return transaction
            
        except Exception as e:
            _logger.debug(f"Error processing row {row_number}: {str(e)}")
            return None
    
    def _parse_date(self, date_value):
        """Parse date from various formats"""
        if not date_value:
            return None
            
        # If it's already a datetime object
        if isinstance(date_value, datetime):
            return date_value.date()
        
        # If it's a date object from datetime
        from datetime import date
        if isinstance(date_value, date):
            return date_value
        
        # If it's a string, try different formats
        if isinstance(date_value, str):
            date_formats = [
                '%d/%m/%Y',
                '%d-%m-%Y', 
                '%Y-%m-%d',
                '%d/%m/%y',
                '%d-%m-%y',
                '%m/%d/%Y',  # US format
                '%m-%d-%Y',  # US format
                '%Y/%m/%d',  # ISO format variant
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_value.strip(), fmt).date()
                except ValueError:
                    continue
        
        # If it's a number (Excel date)
        if isinstance(date_value, (int, float)):
            try:
                # Excel date starts from 1900-01-01
                from datetime import timedelta
                excel_base = datetime(1900, 1, 1)
                # Excel incorrectly considers 1900 as leap year, so subtract 2
                delta = timedelta(days=int(date_value) - 2)
                return (excel_base + delta).date()
            except:
                pass
        
        return None
    
    def _parse_amount(self, amount_value):
        """Parse amount from various formats"""
        if not amount_value:
            return 0.0
            
        # If it's already a number
        if isinstance(amount_value, (int, float)):
            return float(amount_value)
        
        # If it's a string, clean and parse
        if isinstance(amount_value, str):
            # Remove currency symbols, spaces
            cleaned = amount_value.strip()
            cleaned = cleaned.replace(' ', '')
            cleaned = cleaned.replace('MZN', '')
            cleaned = cleaned.replace('MT', '')
            cleaned = cleaned.replace('Mts', '')
            
            # Handle different decimal/thousand separators
            # Check if we have both . and ,
            if '.' in cleaned and ',' in cleaned:
                # Determine which is thousand separator
                dot_pos = cleaned.rfind('.')
                comma_pos = cleaned.rfind(',')
                
                if dot_pos > comma_pos:
                    # . is decimal separator, , is thousand separator
                    cleaned = cleaned.replace(',', '')
                else:
                    # , is decimal separator, . is thousand separator
                    cleaned = cleaned.replace('.', '')
                    cleaned = cleaned.replace(',', '.')
            elif ',' in cleaned:
                # Only comma present - could be decimal or thousand separator
                # If there are 2 digits after comma, likely decimal
                parts = cleaned.split(',')
                if len(parts) == 2 and len(parts[1]) == 2:
                    cleaned = cleaned.replace(',', '.')
                else:
                    # Likely thousand separator
                    cleaned = cleaned.replace(',', '')
            
            # Handle parentheses for negative numbers
            if cleaned.startswith('(') and cleaned.endswith(')'):
                cleaned = '-' + cleaned[1:-1]
            
            try:
                return float(cleaned)
            except ValueError:
                return 0.0
        
        return 0.0
    
    def _format_for_odoo_import(self, transactions, bank_type="bim"):
        """
        Format transactions for Odoo import
        Returns data in XLSX format for the full import interface
        """
        if not transactions:
            raise UserError("Nenhuma transação válida encontrada no arquivo.")
        
        # Sort transactions by date
        transactions.sort(key=lambda x: x['date'])
        
        # Create a new workbook with formatted data
        wb = openpyxl.Workbook()
        sheet = wb.active
        sheet.title = "Bank Statement"
        
        # Write headers that match account.bank.statement.line fields
        headers = ['Date', 'Label', 'Amount']
        for col, header in enumerate(headers, 1):
            sheet.cell(row=1, column=col, value=header)
        
        # Write transactions
        for row_idx, trans in enumerate(transactions, 2):
            sheet.cell(row=row_idx, column=1, value=trans['date'].strftime('%Y-%m-%d'))
            sheet.cell(row=row_idx, column=2, value=trans['payment_ref'])
            sheet.cell(row=row_idx, column=3, value=trans['amount'])
        
        # Save to BytesIO
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        # Encode to base64
        xlsx_base64 = base64.b64encode(output.read())
        
        return {
            'file': xlsx_base64,
            'file_name': f'{bank_type}_formatted_statement.xlsx',
            'file_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'transaction_count': len(transactions),
            'total_debit': sum(t['amount'] for t in transactions if t['amount'] < 0),
            'total_credit': sum(t['amount'] for t in transactions if t['amount'] > 0),
        }
    
    # Stub methods for XLS and CSV (copy from original)
    def _parse_xls(self, file_data):
        """Parse XLS file format (BCI format)"""
        if not xlrd:
            raise UserError("XLS format not supported (xlrd library not available). Please convert to XLSX format.")
        
        try:
            _logger.info("BIM Parser: _parse_xls called for BCI format")
            file_stream = io.BytesIO(file_data)
            
            # Open XLS file with xlrd
            workbook = xlrd.open_workbook(file_contents=file_data)
            _logger.info(f"BIM Parser: XLS workbook opened, sheets: {workbook.sheet_names()}")
            
            # Use first sheet (usually 'Extracto' for BCI)
            sheet = workbook.sheet_by_index(0)
            _logger.info(f"BIM Parser: Sheet '{sheet.name}' with {sheet.nrows} rows, {sheet.ncols} columns")
            
            # Extract BCI header information
            bci_info = self._extract_bci_header_info(sheet)
            
            transactions = []
            
            # Process BCI transactions starting from row 10 (index 9)
            for row_idx in range(9, sheet.nrows):  # Start from row 10 (index 9)
                row_values = []
                for col_idx in range(sheet.ncols):
                    cell = sheet.cell(row_idx, col_idx)
                    row_values.append(cell.value)
                
                # Skip empty rows
                if not row_values or all(not v for v in row_values):
                    continue
                    
                transaction = self._process_bci_row(row_values, row_idx + 1)
                if transaction:
                    transactions.append(transaction)
                    _logger.info(f"BIM Parser: BCI Transaction added from row {row_idx + 1}: {transaction}")
            
            _logger.info(f"BIM Parser: BCI processed {sheet.nrows} rows, found {len(transactions)} transactions")
            
            if not transactions:
                _logger.warning("BIM Parser: No BCI transactions found!")
                # Log some sample rows for debugging
                for i in range(min(15, sheet.nrows)):
                    row = [sheet.cell(i, j).value for j in range(min(8, sheet.ncols))]
                    _logger.warning(f"  BCI Sample row {i + 1}: {row}")
            
            result = self._format_for_odoo_import(transactions, "bci")
            _logger.info(f"BIM Parser: BCI formatted result with {result.get('transaction_count')} transactions")
            
            # Add BCI header information to result
            if bci_info:
                result['bci_info'] = bci_info
                # Add first and last transaction info
                if transactions:
                    result['bci_info']['first_transaction'] = transactions[0] if transactions else None
                    result['bci_info']['last_transaction'] = transactions[-1] if transactions else None
            
            return result
            
        except Exception as e:
            _logger.error(f"Erro ao processar XLS BCI: {str(e)}")
            import traceback
            _logger.error(traceback.format_exc())
            raise UserError(f"Erro ao processar arquivo XLS BCI: {str(e)}")
    
    def _process_bci_row(self, row, row_number):
        """Process a single row from BCI statement (XLS format)"""
        try:
            _logger.debug(f"Processing BCI row {row_number}: {row[:8]}")
            
            # BCI XLS format columns:
            # A: Data Mov. (ex: '01-08-2025')
            # B: Número de Documento 
            # C: Num. Oper.
            # D: Data Valor 
            # E: Descrição
            # F: Valor (ex: '+519,00', '-400.000,00') 
            # G: Saldo
            # H: Moeda
            
            if len(row) < 6:
                return None
                
            transaction_date = row[0] if row[0] else None
            document_number = row[1] if len(row) > 1 else ""
            operation_number = row[2] if len(row) > 2 else ""
            value_date = row[3] if len(row) > 3 else None
            description = row[4] if len(row) > 4 else ""
            amount_str = row[5] if len(row) > 5 else "0"
            balance_str = row[6] if len(row) > 6 else "0"
            currency = row[7] if len(row) > 7 else "MZN"
            
            # Skip if no date
            if not transaction_date:
                return None
            
            # Skip header rows
            if isinstance(transaction_date, str) and any(header in transaction_date.lower() for header in ['data', 'mov']):
                return None
            
            # Parse date 
            date_obj = self._parse_date(transaction_date)
            if not date_obj:
                _logger.debug(f"Could not parse BCI date in row {row_number}: {transaction_date}")
                return None
            
            # Parse amount - BCI format uses Portuguese number format
            amount = self._parse_bci_amount(amount_str)
            if amount == 0:
                return None
            
            # Create transaction
            transaction = {
                'date': date_obj,
                'payment_ref': f"{description} (Doc: {document_number})".strip(),
                'amount': amount,
                'balance': self._parse_bci_amount(balance_str),
                'row_number': row_number
            }
            
            return transaction
            
        except Exception as e:
            _logger.debug(f"Error processing BCI row {row_number}: {str(e)}")
            return None
    
    def _parse_bci_amount(self, amount_str):
        """Parse BCI amount format (Portuguese: +519,00 or -400.000,00)"""
        if not amount_str:
            return 0.0
            
        # If it's already a number
        if isinstance(amount_str, (int, float)):
            return float(amount_str)
        
        # Clean string
        cleaned = str(amount_str).strip()
        
        # Remove currency and spaces
        cleaned = cleaned.replace('MZN', '').replace(' ', '').strip()
        
        # Handle sign
        negative = cleaned.startswith('-')
        if cleaned.startswith(('+', '-')):
            cleaned = cleaned[1:]
        
        # BCI uses Portuguese format:
        # - Thousands separator: . (dot)
        # - Decimal separator: , (comma)
        # Example: 400.000,00 = 400000.00
        
        # Replace decimal comma with dot
        if ',' in cleaned:
            # Find last comma (should be decimal separator)
            parts = cleaned.rsplit(',', 1)
            if len(parts) == 2 and len(parts[1]) <= 2:
                # This is likely decimal separator
                integer_part = parts[0].replace('.', '')  # Remove thousand separators
                decimal_part = parts[1]
                cleaned = f"{integer_part}.{decimal_part}"
            else:
                # No decimal part or unusual format
                cleaned = cleaned.replace(',', '').replace('.', '')
        else:
            # No comma, remove dots (thousand separators)
            cleaned = cleaned.replace('.', '')
        
        try:
            amount = float(cleaned)
            return -amount if negative else amount
        except ValueError:
            _logger.warning(f"Could not parse BCI amount: {amount_str}")
            return 0.0
    
    def _parse_csv(self, file_data):
        """Parse CSV file format"""
        raise UserError("CSV format not yet implemented in debug version")
    
    def _parse_card_csv(self, file_data):
        """Parse CARD CSV file format (Portuguese format with semicolon separator)"""
        try:
            _logger.info("BIM Parser: _parse_card_csv called")
            
            # Decode with latin-1 encoding (Portuguese characters)
            content = file_data.decode('latin-1')
            lines = content.strip().split('\n')
            
            _logger.info(f"BIM Parser: CARD CSV has {len(lines)} lines")
            
            transactions = []
            
            # Skip header (line 1) and process data lines
            for line_idx, line in enumerate(lines[1:], start=2):
                if not line.strip():
                    continue
                
                # Split by semicolon
                cols = line.split(';')
                if len(cols) < 5:
                    _logger.debug(f"CARD CSV: Skipping line {line_idx}, not enough columns: {len(cols)}")
                    continue
                
                transaction = self._process_card_csv_row(cols, line_idx)
                if transaction:
                    transactions.append(transaction)
                    _logger.info(f"BIM Parser: CARD CSV Transaction added from line {line_idx}: {transaction}")
            
            _logger.info(f"BIM Parser: CARD CSV processed {len(lines)} lines, found {len(transactions)} transactions")
            
            if not transactions:
                raise UserError("Nenhuma transação de cartão válida encontrada no arquivo CSV.")
            
            result = self._format_for_odoo_import(transactions, "card")
            _logger.info(f"BIM Parser: CARD CSV formatted result with {result.get('transaction_count')} transactions")
            return result
            
        except Exception as e:
            _logger.error(f"Erro ao processar CSV CARD: {str(e)}")
            import traceback
            _logger.error(traceback.format_exc())
            raise UserError(f"Erro ao processar arquivo CSV CARD: {str(e)}")
    
    def _process_card_csv_row(self, cols, row_number):
        """Process a single row from CARD CSV statement"""
        try:
            _logger.debug(f"Processing CARD CSV row {row_number}: {cols[:5]}")
            
            # CARD CSV format columns:
            # 0: Lançamento de dados (DD/MM/YYYY)
            # 1: Valor dos dados (DD/MM/YYYY) 
            # 2: Descrição
            # 3: Montante (Portuguese format: -3 897,59)
            # 4: Monte Original (with € symbol)
            
            transaction_date_str = cols[0].strip() if cols[0] else None
            value_date_str = cols[1].strip() if len(cols) > 1 else None
            description = cols[2].strip() if len(cols) > 2 else ""
            amount_str = cols[3].strip() if len(cols) > 3 else "0"
            
            # Skip if no date
            if not transaction_date_str:
                return None
            
            # Parse date
            date_obj = self._parse_date(transaction_date_str)
            if not date_obj:
                _logger.debug(f"Could not parse CARD CSV date in row {row_number}: {transaction_date_str}")
                return None
            
            # Parse amount - Portuguese format
            amount = self._parse_card_amount(amount_str)
            if amount == 0:
                return None
            
            # Create transaction
            transaction = {
                'date': date_obj,
                'payment_ref': description,
                'amount': amount,
                'row_number': row_number
            }
            
            return transaction
            
        except Exception as e:
            _logger.debug(f"Error processing CARD CSV row {row_number}: {str(e)}")
            return None
    
    def _parse_card_xls(self, file_data):
        """Parse CARD XLS file format"""
        if not xlrd:
            raise UserError("XLS format not supported (xlrd library not available). Please convert to CSV format.")
        
        try:
            _logger.info("BIM Parser: _parse_card_xls called")
            
            # Open XLS file with xlrd
            workbook = xlrd.open_workbook(file_contents=file_data)
            _logger.info(f"BIM Parser: CARD XLS workbook opened, sheets: {workbook.sheet_names()}")
            
            # Use first sheet
            sheet = workbook.sheet_by_index(0)
            _logger.info(f"BIM Parser: CARD XLS Sheet '{sheet.name}' with {sheet.nrows} rows, {sheet.ncols} columns")
            
            transactions = []
            
            # Process CARD XLS transactions starting from row 7 (index 6)
            for row_idx in range(6, sheet.nrows):  # Start from row 7 (index 6)
                row_values = []
                for col_idx in range(sheet.ncols):
                    cell = sheet.cell(row_idx, col_idx)
                    row_values.append(cell.value)
                
                # Skip empty rows
                if not row_values or all(not v for v in row_values):
                    continue
                    
                transaction = self._process_card_xls_row(row_values, row_idx + 1)
                if transaction:
                    transactions.append(transaction)
                    _logger.info(f"BIM Parser: CARD XLS Transaction added from row {row_idx + 1}: {transaction}")
            
            _logger.info(f"BIM Parser: CARD XLS processed {sheet.nrows} rows, found {len(transactions)} transactions")
            
            if not transactions:
                _logger.warning("BIM Parser: No CARD XLS transactions found!")
                # Log some sample rows for debugging
                for i in range(min(10, sheet.nrows)):
                    row = [sheet.cell(i, j).value for j in range(min(7, sheet.ncols))]
                    _logger.warning(f"  CARD XLS Sample row {i + 1}: {row}")
            
            result = self._format_for_odoo_import(transactions, "card")
            _logger.info(f"BIM Parser: CARD XLS formatted result with {result.get('transaction_count')} transactions")
            return result
            
        except Exception as e:
            _logger.error(f"Erro ao processar XLS CARD: {str(e)}")
            import traceback
            _logger.error(traceback.format_exc())
            raise UserError(f"Erro ao processar arquivo XLS CARD: {str(e)}")
    
    def _process_card_xls_row(self, row, row_number):
        """Process a single row from CARD XLS statement"""
        try:
            _logger.debug(f"Processing CARD XLS row {row_number}: {row[:7]}")
            
            # CARD XLS format columns:
            # 0: Data Mov. (ex: '01-08-2025')
            # 1: Data Valor (ex: '01/08/2025') 
            # 2: Descrição
            # 3: Valor (ex: '-1.945,30')
            # 4: Moeda (ex: 'MZN')
            # 5: Saldo 
            # 6: Moeda
            
            if len(row) < 4:
                return None
                
            transaction_date = row[0] if row[0] else None
            value_date = row[1] if len(row) > 1 else None
            description = row[2] if len(row) > 2 else ""
            amount_str = row[3] if len(row) > 3 else "0"
            currency = row[4] if len(row) > 4 else "MZN"
            
            # Skip if no date
            if not transaction_date:
                return None
            
            # Skip header rows
            if isinstance(transaction_date, str) and any(header in transaction_date.lower() for header in ['data', 'mov']):
                return None
            
            # Parse date 
            date_obj = self._parse_date(transaction_date)
            if not date_obj:
                _logger.debug(f"Could not parse CARD XLS date in row {row_number}: {transaction_date}")
                return None
            
            # Parse amount - Portuguese format
            amount = self._parse_card_amount(amount_str)
            if amount == 0:
                return None
            
            # Create transaction
            transaction = {
                'date': date_obj,
                'payment_ref': str(description).strip(),
                'amount': amount,
                'row_number': row_number
            }
            
            return transaction
            
        except Exception as e:
            _logger.debug(f"Error processing CARD XLS row {row_number}: {str(e)}")
            return None
    
    def _parse_card_amount(self, amount_str):
        """Parse CARD amount format (Portuguese: -3 897,59 or +10.000,00)"""
        if not amount_str:
            return 0.0
            
        # If it's already a number
        if isinstance(amount_str, (int, float)):
            return float(amount_str)
        
        # Clean string
        cleaned = str(amount_str).strip()
        
        # Remove currency symbols and extra characters
        cleaned = cleaned.replace('€', '').replace('MZN', '').replace(' ', '').strip()
        cleaned = cleaned.replace('�', '').replace('"', '').replace('"', '')
        
        # Handle sign
        negative = cleaned.startswith('-')
        positive_sign = cleaned.startswith('+')
        if cleaned.startswith(('+', '-')):
            cleaned = cleaned[1:]
        
        # Portuguese format can have:
        # - Space as thousand separator: -3 897,59
        # - Dot as thousand separator: 10.000,00
        # - Comma as decimal separator: ,59
        
        # First, handle decimal comma
        if ',' in cleaned:
            parts = cleaned.rsplit(',', 1)
            if len(parts) == 2 and len(parts[1]) <= 2:
                # This is decimal separator
                integer_part = parts[0]
                decimal_part = parts[1]
                
                # Remove thousand separators from integer part
                integer_part = integer_part.replace('.', '').replace(' ', '')
                cleaned = f"{integer_part}.{decimal_part}"
            else:
                # No decimal part, just remove commas
                cleaned = cleaned.replace(',', '')
        
        # Remove any remaining spaces and dots (thousand separators)
        if '.' in cleaned:
            # Check if dot is decimal separator (last dot with 1-2 digits after)
            parts = cleaned.rsplit('.', 1)
            if len(parts) == 2 and len(parts[1]) <= 2 and parts[1].isdigit():
                # This is decimal separator, remove thousand separators from first part
                integer_part = parts[0].replace('.', '').replace(' ', '')
                cleaned = f"{integer_part}.{parts[1]}"
            else:
                # These are thousand separators
                cleaned = cleaned.replace('.', '').replace(' ', '')
        else:
            cleaned = cleaned.replace(' ', '')
        
        try:
            amount = float(cleaned)
            if negative:
                return -amount
            elif positive_sign:
                return amount
            else:
                return amount
        except ValueError:
            _logger.warning(f"Could not parse CARD amount: {amount_str} -> {cleaned}")
            return 0.0