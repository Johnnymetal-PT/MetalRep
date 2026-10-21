from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import logging
import tempfile
import os
import io
import json
from datetime import datetime
try:
    import openpyxl
except ImportError:
    openpyxl = None
from ..models.bim_parser import BIMStatementParser

_logger = logging.getLogger(__name__)


class BankStatementImportWizard(models.TransientModel):
    _name = 'bank.statement.import.wizard'
    _description = 'Bank Statement Import Wizard'

    # Estados do wizard
    state = fields.Selection([
        ('upload', 'Upload'),
        ('preview', 'Preview'),
        ('mapping', 'Mapeamento'),
        ('processing', 'Processando'),
        ('done', 'Concluído')
    ], default='upload', string='Estado')
    
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
    
    # Preview de dados
    preview_data = fields.Text(
        string='Dados do Preview',
        readonly=True
    )
    preview_lines_count = fields.Integer(
        string='Linhas no Preview',
        default=5
    )
    total_lines_count = fields.Integer(
        string='Total de Linhas',
        readonly=True
    )
    show_all_preview = fields.Boolean(
        string='Mostrar Todas as Linhas',
        default=False
    )
    
    # Campos específicos para BIM - Integridade dos dados
    bim_initial_balance = fields.Float(
        string='Saldo Inicial',
        readonly=True,
        help='Saldo inicial do extrato BIM'
    )
    bim_final_balance = fields.Float(
        string='Saldo Final',
        readonly=True,
        help='Saldo final do extrato BIM'
    )
    bim_first_line = fields.Text(
        string='Primeira Transação',
        readonly=True,
        help='Primeira linha do extrato para validação'
    )
    bim_last_line = fields.Text(
        string='Última Transação',
        readonly=True,
        help='Última linha do extrato para validação'
    )
    bim_period_start = fields.Date(
        string='Data Inicial',
        readonly=True
    )
    bim_period_end = fields.Date(
        string='Data Final',
        readonly=True
    )
    
    # Campos específicos para BCI - Integridade dos dados
    bci_account_number = fields.Char(
        string='Número da Conta',
        readonly=True,
        help='Número da conta BCI'
    )
    bci_available_balance = fields.Float(
        string='Saldo Disponível',
        readonly=True,
        help='Saldo disponível da conta BCI'
    )
    bci_accounting_balance = fields.Float(
        string='Saldo Contabilístico',
        readonly=True,
        help='Saldo contabilístico da conta BCI'
    )
    bci_first_line = fields.Text(
        string='Primeira Transação',
        readonly=True,
        help='Primeira linha do extrato BCI para validação'
    )
    bci_last_line = fields.Text(
        string='Última Transação',
        readonly=True,
        help='Última linha do extrato BCI para validação'
    )
    bci_period_start = fields.Date(
        string='Data Inicial',
        readonly=True
    )
    bci_period_end = fields.Date(
        string='Data Final',
        readonly=True
    )
    
    # Validação de duplicatas
    check_duplicates = fields.Boolean(
        string='Verificar Duplicatas',
        default=True,
        help='Verifica se já existem transações com a mesma data e valor'
    )
    duplicate_count = fields.Integer(
        string='Duplicatas Encontradas',
        readonly=True
    )
    duplicate_action = fields.Selection([
        ('skip', 'Pular Duplicatas'),
        ('import', 'Importar Mesmo Assim'),
        ('review', 'Revisar Uma por Uma')
    ], string='Ação para Duplicatas', default='skip')
    duplicate_details = fields.Text(
        string='Detalhes das Duplicatas',
        readonly=True
    )
    
    # Mapeamento de campos
    enable_field_mapping = fields.Boolean(
        string='Personalizar Mapeamento',
        default=False
    )
    field_mapping = fields.Text(
        string='Mapeamento JSON',
        default='{}',
        help='Mapeamento de campos em formato JSON'
    )
    date_column = fields.Selection(
        selection='_get_column_selection',
        string='Coluna de Data'
    )
    description_column = fields.Selection(
        selection='_get_column_selection',
        string='Coluna de Descrição'
    )
    amount_column = fields.Selection(
        selection='_get_column_selection',
        string='Coluna de Valor'
    )
    
    # Progresso
    progress_percentage = fields.Float(
        string='Progresso (%)',
        readonly=True
    )
    progress_message = fields.Char(
        string='Status',
        readonly=True
    )
    is_processing = fields.Boolean(
        string='Processando',
        default=False
    )
    
    # Relatório de importação
    import_summary = fields.Html(
        string='Resumo da Importação',
        readonly=True
    )
    lines_processed = fields.Integer(
        string='Linhas Processadas',
        readonly=True
    )
    lines_imported = fields.Integer(
        string='Linhas Importadas',
        readonly=True
    )
    lines_skipped = fields.Integer(
        string='Linhas Puladas',
        readonly=True
    )
    lines_error = fields.Integer(
        string='Linhas com Erro',
        readonly=True
    )
    import_log = fields.Text(
        string='Log de Importação',
        readonly=True
    )
    
    # Dados processados (para armazenar entre estados)
    processed_data = fields.Text(
        string='Dados Processados',
        readonly=True
    )
    
    
    @api.model
    def _get_column_selection(self):
        """Retorna seleção de colunas baseada no arquivo carregado"""
        # Esta função será chamada dinamicamente
        return [
            ('0', 'Coluna A'),
            ('1', 'Coluna B'),
            ('2', 'Coluna C'),
            ('3', 'Coluna D'),
            ('4', 'Coluna E'),
            ('5', 'Coluna F'),
        ]
    
    @api.onchange('bank_type')
    def _onchange_bank_type(self):
        """Atualiza mensagem quando banco é selecionado"""
        if self.bank_type:
            bank_name = dict(self._fields['bank_type'].selection).get(self.bank_type)
            self.message = f"Banco selecionado: {bank_name}\n\nAgora faça upload do arquivo do extrato."
    
    @api.onchange('data_file', 'file_name')
    def _onchange_data_file(self):
        """Atualiza mensagem quando arquivo é carregado e prepara preview"""
        if self.data_file and self.file_name:
            if self.bank_type:
                bank_name = dict(self._fields['bank_type'].selection).get(self.bank_type)
                self.message = f"Banco: {bank_name}\nArquivo: {self.file_name}\n\nClique em 'Analisar Arquivo' para ver o preview."
            else:
                self.message = f"Arquivo: {self.file_name}\n\nPor favor, selecione o banco."
    
    @api.onchange('show_all_preview')
    def _onchange_show_all_preview(self):
        """Atualiza o preview quando a opção de mostrar tudo é alterada"""
        if self.state == 'preview' and self.processed_data:
            self._update_preview_display()
    
    def _update_preview_display(self):
        """Atualiza a exibição do preview baseado nas configurações"""
        if not self.processed_data:
            return
            
        try:
            data = json.loads(self.processed_data)
            transactions = data.get('transactions', [])
            
            if not transactions:
                self.preview_data = "Nenhuma transação encontrada no arquivo."
                return
            
            # Determina quantas linhas mostrar
            if self.show_all_preview:
                lines_to_show = len(transactions)
            else:
                lines_to_show = min(self.preview_lines_count, len(transactions))
            
            # Cria o preview
            preview_lines = []
            preview_lines.append("=" * 100)
            preview_lines.append(f"PREVIEW DOS DADOS ({lines_to_show} de {len(transactions)} transações)")
            preview_lines.append("=" * 100)
            preview_lines.append("")
            
            # Cabeçalho da tabela
            preview_lines.append(f"{'Data':<12} | {'Descrição':<40} | {'Valor':>15} | {'Status':<20}")
            preview_lines.append("-" * 100)
            
            # Linhas de dados
            for i, trans in enumerate(transactions[:lines_to_show]):
                date_str = trans.get('date', '')
                desc = trans.get('payment_ref', '')[:40]
                amount = trans.get('amount', 0)
                
                # Verifica se é duplicata
                status = ""
                if self.check_duplicates and trans.get('is_duplicate'):
                    status = "⚠️ DUPLICATA"
                
                # Formata valor
                amount_str = f"{amount:,.2f}".replace(',', '.')
                if amount < 0:
                    amount_str = f"({amount_str[1:]})"  # Remove o sinal e coloca entre parênteses
                
                preview_lines.append(f"{date_str:<12} | {desc:<40} | {amount_str:>15} | {status:<20}")
            
            # Adiciona opção de mostrar mais se necessário
            if not self.show_all_preview and len(transactions) > lines_to_show:
                preview_lines.append("")
                preview_lines.append(f"... mais {len(transactions) - lines_to_show} transações não mostradas ...")
                preview_lines.append("(Marque 'Mostrar Todas as Linhas' para ver o arquivo completo)")
            
            # Resumo
            preview_lines.append("")
            preview_lines.append("=" * 100)
            preview_lines.append("RESUMO")
            preview_lines.append("-" * 100)
            total_debit = sum(t['amount'] for t in transactions if t['amount'] < 0)
            total_credit = sum(t['amount'] for t in transactions if t['amount'] > 0)
            preview_lines.append(f"Total de Transações: {len(transactions)}")
            preview_lines.append(f"Total de Débitos: {total_debit:,.2f}".replace(',', '.'))
            preview_lines.append(f"Total de Créditos: {total_credit:,.2f}".replace(',', '.'))
            preview_lines.append(f"Saldo Final: {(total_credit + total_debit):,.2f}".replace(',', '.'))
            
            if self.duplicate_count > 0:
                preview_lines.append("")
                preview_lines.append(f"⚠️ ATENÇÃO: {self.duplicate_count} possíveis duplicatas encontradas!")
            
            self.preview_data = "\n".join(preview_lines)
            
        except Exception as e:
            self.preview_data = f"Erro ao gerar preview: {str(e)}"
    
    def action_analyze_file(self):
        """Analisa o arquivo e mostra preview"""
        self.ensure_one()
        
        if not self.bank_type:
            raise UserError('Por favor, selecione o banco.')
        
        if not self.data_file:
            raise UserError('Por favor, selecione um arquivo para importar.')
        
        # Atualiza estado
        self.state = 'preview'
        self.progress_percentage = 10
        self.progress_message = "Analisando arquivo..."
        
        # Validação: verifica se existe journal para o banco selecionado
        if self.bank_type:
            test_journal = self._get_journal_by_bank_type()
            if not test_journal:
                # Mensagem de aviso mas não bloqueia
                type_config = {
                    'bim': ('Banco', 'Bank', 'BIM'),
                    'bci': ('Banco', 'Bank', 'BCI'),
                    'card': ('Cartão de Crédito', 'Credit', 'CARD ou CARTAO')
                }
                
                tipo_desc, tipo_sistema, codigo_esperado = type_config.get(self.bank_type, ('', '', ''))
                
                self.message = (
                    f'⚠️ ATENÇÃO: Não foi encontrado um diário do tipo {tipo_desc}.\n\n'
                    f'Para importar corretamente, configure um diário com:\n'
                    f'• Tipo: {tipo_sistema}\n'
                    f'• Código: {codigo_esperado}\n'
                    f'• Nome: Sugestão "{self.dict_bank_type_display[self.bank_type]}"\n\n'
                    f'Vá em: Contabilidade → Configuração → Diários\n\n'
                    f'Você pode continuar, mas precisará configurar o diário antes de importar.'
                )
                _logger.warning(f"Journal não encontrado para {self.bank_type}")
            else:
                _logger.info(f"Journal encontrado para {self.bank_type}: {test_journal.name}")
        
        try:
            # Processa o arquivo
            parser = BIMStatementParser()
            formatted_data = parser.parse_file(self.data_file, self.file_name, self.bank_type)
            
            # Se for BIM, extrai informações adicionais
            if self.bank_type == 'bim' and 'bim_info' in formatted_data:
                bim_info = formatted_data['bim_info']
                
                # Preenche campos BIM
                if 'initial_balance' in bim_info:
                    self.bim_initial_balance = self._convert_to_float(bim_info['initial_balance'])
                if 'final_balance' in bim_info:
                    self.bim_final_balance = self._convert_to_float(bim_info['final_balance'])
                    
                # Período
                if 'period_start' in bim_info:
                    try:
                        from datetime import datetime
                        date_str = bim_info['period_start'].replace('-', '/')
                        self.bim_period_start = datetime.strptime(date_str, '%d/%m/%Y').date()
                    except:
                        pass
                if 'period_end' in bim_info:
                    try:
                        from datetime import datetime
                        date_str = bim_info['period_end'].replace('-', '/')
                        self.bim_period_end = datetime.strptime(date_str, '%d/%m/%Y').date()
                    except:
                        pass
                
                # Primeira e última transação
                if 'first_transaction' in bim_info:
                    ft = bim_info['first_transaction']
                    # Formata a data corretamente
                    if hasattr(ft['date'], 'strftime'):
                        date_str = ft['date'].strftime('%d/%m/%Y')
                    elif isinstance(ft['date'], str) and '-' in ft['date']:
                        # Se já é string no formato YYYY-MM-DD, converte para DD/MM/YYYY
                        parts = ft['date'].split('-')
                        if len(parts) == 3:
                            date_str = f"{parts[2]}/{parts[1]}/{parts[0]}"
                        else:
                            date_str = str(ft['date'])
                    else:
                        date_str = str(ft['date'])
                    amount = ft['debit'] or ft['credit'] or 0
                    desc = ft.get('description', '')[:50] if ft.get('description') else ''
                    self.bim_first_line = f"Data: {date_str} | {desc} | Valor: {amount}"
                    
                if 'last_transaction' in bim_info:
                    lt = bim_info['last_transaction']
                    # Formata a data corretamente
                    if hasattr(lt['date'], 'strftime'):
                        date_str = lt['date'].strftime('%d/%m/%Y')
                    elif isinstance(lt['date'], str) and '-' in lt['date']:
                        # Se já é string no formato YYYY-MM-DD, converte para DD/MM/YYYY
                        parts = lt['date'].split('-')
                        if len(parts) == 3:
                            date_str = f"{parts[2]}/{parts[1]}/{parts[0]}"
                        else:
                            date_str = str(lt['date'])
                    else:
                        date_str = str(lt['date'])
                    amount = lt['debit'] or lt['credit'] or 0
                    desc = lt.get('description', '')[:50] if lt.get('description') else ''
                    self.bim_last_line = f"Data: {date_str} | {desc} | Valor: {amount}"
            
            # Se for BCI, extrai informações adicionais
            if self.bank_type == 'bci' and 'bci_info' in formatted_data:
                bci_info = formatted_data['bci_info']
                
                # Preenche campos BCI
                if 'account_number' in bci_info:
                    self.bci_account_number = bci_info['account_number']
                    
                if 'available_balance' in bci_info:
                    self.bci_available_balance = self._convert_to_float(bci_info['available_balance'])
                    
                if 'accounting_balance' in bci_info:
                    self.bci_accounting_balance = self._convert_to_float(bci_info['accounting_balance'])
                    
                # Período
                if 'period_start' in bci_info:
                    try:
                        from datetime import datetime
                        date_str = bci_info['period_start'].replace('-', '/')
                        self.bci_period_start = datetime.strptime(date_str, '%d/%m/%Y').date()
                    except:
                        pass
                if 'period_end' in bci_info:
                    try:
                        from datetime import datetime
                        date_str = bci_info['period_end'].replace('-', '/')
                        self.bci_period_end = datetime.strptime(date_str, '%d/%m/%Y').date()
                    except:
                        pass
                
                # Primeira e última transação
                if 'first_transaction' in bci_info:
                    ft = bci_info['first_transaction']
                    # Formata a data corretamente
                    if hasattr(ft.get('date'), 'strftime'):
                        date_str = ft['date'].strftime('%d/%m/%Y')
                    elif isinstance(ft.get('date'), str):
                        date_str = ft['date']
                    else:
                        date_str = str(ft.get('date', ''))
                    desc = ft.get('payment_ref', '')[:50] if ft.get('payment_ref') else ''
                    amount = ft.get('amount', 0)
                    self.bci_first_line = f"Data: {date_str} | {desc} | Valor: {amount}"
                    
                if 'last_transaction' in bci_info:
                    lt = bci_info['last_transaction']
                    # Formata a data corretamente
                    if hasattr(lt.get('date'), 'strftime'):
                        date_str = lt['date'].strftime('%d/%m/%Y')
                    elif isinstance(lt.get('date'), str):
                        date_str = lt['date']
                    else:
                        date_str = str(lt.get('date', ''))
                    desc = lt.get('payment_ref', '')[:50] if lt.get('payment_ref') else ''
                    amount = lt.get('amount', 0)
                    self.bci_last_line = f"Data: {date_str} | {desc} | Valor: {amount}"
            
            # Decodifica o arquivo formatado para extrair as transações
            xlsx_data = base64.b64decode(formatted_data['file'])
            wb = openpyxl.load_workbook(io.BytesIO(xlsx_data))
            sheet = wb.active
            
            transactions = []
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if row and row[0]:
                    trans = {
                        'date': row[0] if isinstance(row[0], str) else row[0].strftime('%Y-%m-%d'),
                        'payment_ref': row[1] or '',
                        'amount': float(row[2]) if row[2] else 0.0,
                        'is_duplicate': False
                    }
                    transactions.append(trans)
            
            # Verifica duplicatas se habilitado
            if self.check_duplicates:
                self._check_for_duplicates(transactions)
            
            # Armazena dados processados incluindo bim_info
            processed_data = {
                'transactions': transactions,
                'bank_type': self.bank_type,
                'file_name': self.file_name,
                'formatted_file': formatted_data['file'].decode('utf-8')
            }
            if 'bim_info' in formatted_data:
                # Converte datetime para string antes de serializar
                bim_info_clean = {}
                for key, value in formatted_data['bim_info'].items():
                    if isinstance(value, dict):
                        # Para first_transaction e last_transaction
                        clean_dict = {}
                        for k, v in value.items():
                            if hasattr(v, 'strftime'):
                                clean_dict[k] = v.strftime('%Y-%m-%d')
                            else:
                                clean_dict[k] = v
                        bim_info_clean[key] = clean_dict
                    elif hasattr(value, 'strftime'):
                        bim_info_clean[key] = value.strftime('%Y-%m-%d')
                    else:
                        bim_info_clean[key] = value
                processed_data['bim_info'] = bim_info_clean
                
            if 'bci_info' in formatted_data:
                # Converte datetime para string antes de serializar
                bci_info_clean = {}
                for key, value in formatted_data['bci_info'].items():
                    if isinstance(value, dict):
                        # Para first_transaction e last_transaction
                        clean_dict = {}
                        for k, v in value.items():
                            if hasattr(v, 'strftime'):
                                clean_dict[k] = v.strftime('%Y-%m-%d')
                            else:
                                clean_dict[k] = v
                        bci_info_clean[key] = clean_dict
                    elif hasattr(value, 'strftime'):
                        bci_info_clean[key] = value.strftime('%Y-%m-%d')
                    else:
                        bci_info_clean[key] = value
                processed_data['bci_info'] = bci_info_clean
                
            self.processed_data = json.dumps(processed_data)
            
            self.total_lines_count = len(transactions)
            self.progress_percentage = 30
            
            # Adiciona informação do journal que será usado
            target_journal = self._get_journal_by_bank_type() if self.bank_type else None
            if target_journal:
                self.progress_message = f"Arquivo analisado! Será importado para: {target_journal.name}"
            else:
                self.progress_message = "Arquivo analisado com sucesso!"
            
            # Atualiza preview
            self._update_preview_display()
            
        except Exception as e:
            self.state = 'upload'
            self.progress_percentage = 0
            raise UserError(f'Erro ao analisar arquivo: {str(e)}')
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'bank.statement.import.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': self.env.context,
        }
    
    def _check_for_duplicates(self, transactions):
        """Verifica se existem transações duplicadas"""
        duplicate_count = 0
        duplicate_details = []
        
        # Tenta obter o journal correto para verificar duplicatas
        journal_id = None
        if self.bank_type:
            journal = self._get_journal_by_bank_type()
            if journal:
                journal_id = journal.id
        
        # Se não encontrou, usa do contexto
        if not journal_id:
            journal_id = self.env.context.get('journal_id', False)
        
        for trans in transactions:
            # Busca por transações existentes com mesma data e valor
            domain = [
                ('date', '=', trans['date']),
                ('amount', '=', trans['amount']),
            ]
            
            # Se tem journal específico, busca apenas nele
            if journal_id:
                domain.append(('journal_id', '=', journal_id))
            
            existing = self.env['account.bank.statement.line'].search(domain, limit=1)
            
            if existing:
                trans['is_duplicate'] = True
                duplicate_count += 1
                duplicate_details.append(f"Data: {trans['date']}, Valor: {trans['amount']}, Ref: {trans['payment_ref'][:30]}")
        
        self.duplicate_count = duplicate_count
        if duplicate_count > 0:
            self.duplicate_details = "\n".join(duplicate_details[:10])  # Mostra no máximo 10
            if duplicate_count > 10:
                self.duplicate_details += f"\n... e mais {duplicate_count - 10} duplicatas"
    
    def action_configure_mapping(self):
        """Vai para tela de configuração de mapeamento"""
        self.ensure_one()
        self.state = 'mapping'
        self.progress_percentage = 40
        self.progress_message = "Configure o mapeamento de campos"
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'bank.statement.import.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': self.env.context,
        }
    
    def _get_journal_by_bank_type(self):
        """
        Busca o journal correspondente ao bank_type selecionado
        Usando os tipos reais do Odoo 18
        """
        self.ensure_one()
        
        # Mapeamento correto dos tipos conforme Odoo 18
        journal_type_map = {
            'bim': 'bank',      # BIM é tipo banco
            'bci': 'bank',      # BCI é tipo banco  
            'card': 'credit'    # CARD é tipo credit (não credit_card)
        }
        
        # Códigos esperados para cada banco
        bank_code_map = {
            'bim': ['BIM', 'bim'],
            'bci': ['BCI', 'bci'],
            'card': ['CARD', 'card', 'CARTAO', 'cartao']
        }
        
        journal_type = journal_type_map.get(self.bank_type)
        possible_codes = bank_code_map.get(self.bank_type, [])
        
        # Busca journal com tipo e código corretos
        journal = self.env['account.journal'].search([
            ('type', '=', journal_type),
            ('code', 'in', possible_codes),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        
        if not journal:
            # Fallback: busca por nome se não encontrar por código
            bank_name_patterns = {
                'bim': ['BIM', 'Millennium', 'Internacional'],
                'bci': ['BCI', 'Comercial', 'Investimentos'],
                'card': ['Card', 'Cartão', 'Cartao', 'Credit', 'Crédito']
            }
            
            for pattern in bank_name_patterns.get(self.bank_type, []):
                journal = self.env['account.journal'].search([
                    ('type', '=', journal_type),
                    ('name', 'ilike', pattern),
                    ('company_id', '=', self.env.company.id)
                ], limit=1)
                if journal:
                    break
        
        return journal
    
    @property
    def dict_bank_type_display(self):
        """Retorna nomes amigáveis para cada bank_type"""
        return {
            'bim': 'BIM - Banco Internacional de Moçambique',
            'bci': 'BCI - Banco Comercial e de Investimentos',
            'card': 'Cartão de Crédito/Débito'
        }
    
    def action_import(self):
        """Processa a importação com todas as melhorias"""
        self.ensure_one()
        
        if not self.processed_data:
            raise UserError('Por favor, analise o arquivo primeiro.')
        
        self.state = 'processing'
        self.is_processing = True
        self.progress_percentage = 50
        self.progress_message = "Iniciando importação..."
        
        try:
            data = json.loads(self.processed_data)
            transactions = data.get('transactions', [])
            
            # Prepara contadores
            imported = 0
            skipped = 0
            errors = 0
            import_log = []
            
            # Obtém journal baseado no bank_type selecionado
            journal = None
            journal_id = None
            
            # Primeiro tenta obter pelo bank_type
            if self.bank_type:
                journal = self._get_journal_by_bank_type()
                if journal:
                    journal_id = journal.id
                    _logger.info(
                        f"Importando {self.bank_type.upper()} para journal: {journal.name} "
                        f"(tipo: {journal.type}, código: {journal.code})"
                    )
                    import_log.append(f"📁 Diário destino: {journal.name} ({journal.type})")
            
            # Se não encontrou, tenta do contexto (comportamento original)
            if not journal_id:
                journal_id = self.env.context.get('journal_id')
                if journal_id:
                    journal = self.env['account.journal'].browse(journal_id)
                    _logger.info(f"Usando journal do contexto: {journal.name}")
            
            # Se ainda não tem, busca qualquer journal bancário (fallback original)
            if not journal_id:
                bank_journal = self.env['account.journal'].search([
                    ('type', '=', 'bank'),
                    ('company_id', '=', self.env.company.id)
                ], limit=1)
                if bank_journal:
                    journal_id = bank_journal.id
                    _logger.info(f"Usando journal bancário padrão: {bank_journal.name}")
            
            # Se ainda não tem journal, mostra erro específico
            if not journal_id:
                if self.bank_type:
                    type_names = {
                        'bim': 'Banco (Bank)',
                        'bci': 'Banco (Bank)',
                        'card': 'Cartão de Crédito (Credit)'
                    }
                    raise UserError(
                        f'❌ Diário não encontrado para {self.bank_type.upper()}\n\n'
                        f'Por favor, configure um diário com:\n'
                        f'• Tipo: {type_names[self.bank_type]}\n'
                        f'• Código: {self.bank_type.upper()}\n\n'
                        f'Acesse: Contabilidade → Configuração → Diários → Novo'
                    )
                else:
                    raise UserError('Nenhum diário bancário foi encontrado. Por favor, configure um diário bancário.')
            
            # Processa cada transação
            total = len(transactions)
            for idx, trans in enumerate(transactions):
                # Atualiza progresso
                progress = 50 + (idx / total * 40)
                self.progress_percentage = progress
                self.progress_message = f"Processando transação {idx + 1} de {total}..."
                
                # Verifica se deve pular duplicata
                if trans.get('is_duplicate') and self.duplicate_action == 'skip':
                    skipped += 1
                    import_log.append(f"PULADA (duplicata): {trans['date']} - {trans['payment_ref'][:30]} - {trans['amount']}")
                    continue
                
                # Cria a linha
                try:
                    line_vals = {
                        'date': trans['date'],
                        'payment_ref': trans['payment_ref'],
                        'amount': trans['amount'],
                    }
                    
                    if journal_id:
                        line_vals['journal_id'] = journal_id
                    
                    line = self.env['account.bank.statement.line'].create(line_vals)
                    imported += 1
                    import_log.append(f"OK: {trans['date']} - {trans['payment_ref'][:30]} - {trans['amount']}")
                    
                except Exception as e:
                    errors += 1
                    import_log.append(f"ERRO: {trans['date']} - {trans['payment_ref'][:30]} - {str(e)}")
            
            # Atualiza estatísticas finais
            self.lines_processed = total
            self.lines_imported = imported
            self.lines_skipped = skipped
            self.lines_error = errors
            self.import_log = "\n".join(import_log[-100:])  # Últimas 100 linhas
            
            # Gera resumo HTML
            self.import_summary = self._generate_import_summary(total, imported, skipped, errors)
            
            # Finaliza
            self.state = 'done'
            self.is_processing = False
            self.progress_percentage = 100
            self.progress_message = "Importação concluída!"
            
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'bank.statement.import.wizard',
                'view_mode': 'form',
                'res_id': self.id,
                'target': 'new',
                'context': self.env.context,
            }
            
        except Exception as e:
            self.state = 'preview'
            self.is_processing = False
            self.progress_percentage = 0
            _logger.error(f"Erro durante importação: {str(e)}")
            raise UserError(f'Erro durante importação: {str(e)}')
    
    def _generate_import_summary(self, total, imported, skipped, errors):
        """Gera um resumo HTML da importação"""
        success_rate = (imported / total * 100) if total > 0 else 0
        
        # Define cor baseada na taxa de sucesso
        if success_rate >= 90:
            color = "success"
            icon = "✅"
        elif success_rate >= 70:
            color = "warning"
            icon = "⚠️"
        else:
            color = "danger"
            icon = "❌"
        
        html = f"""
        <div style="padding: 20px; background-color: #f8f9fa; border-radius: 8px;">
            <h3 style="color: #333; margin-bottom: 20px;">
                {icon} Resumo da Importação
            </h3>
            
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 20px;">
                <div style="background: white; padding: 15px; border-radius: 5px; border-left: 4px solid #28a745;">
                    <div style="color: #666; font-size: 12px;">Importadas com Sucesso</div>
                    <div style="font-size: 24px; font-weight: bold; color: #28a745;">{imported}</div>
                </div>
                
                <div style="background: white; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107;">
                    <div style="color: #666; font-size: 12px;">Puladas (Duplicatas)</div>
                    <div style="font-size: 24px; font-weight: bold; color: #ffc107;">{skipped}</div>
                </div>
                
                <div style="background: white; padding: 15px; border-radius: 5px; border-left: 4px solid #dc3545;">
                    <div style="color: #666; font-size: 12px;">Erros</div>
                    <div style="font-size: 24px; font-weight: bold; color: #dc3545;">{errors}</div>
                </div>
                
                <div style="background: white; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff;">
                    <div style="color: #666; font-size: 12px;">Total Processado</div>
                    <div style="font-size: 24px; font-weight: bold; color: #007bff;">{total}</div>
                </div>
            </div>
            
            <div style="background: white; padding: 15px; border-radius: 5px;">
                <div style="color: #666; margin-bottom: 10px;">Taxa de Sucesso</div>
                <div style="background: #e9ecef; border-radius: 3px; overflow: hidden;">
                    <div style="background: #28a745; height: 30px; width: {success_rate}%; 
                                display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                        {success_rate:.1f}%
                    </div>
                </div>
            </div>
            
            <div style="margin-top: 20px; padding: 15px; background: #e7f3ff; border-radius: 5px;">
                <strong>Próximos Passos:</strong>
                <ul style="margin-top: 10px; margin-bottom: 0;">
                    <li>Acesse o menu Faturamento → Diários para reconciliar as transações</li>
                    <li>Verifique o log abaixo para detalhes sobre erros ou transações puladas</li>
                </ul>
            </div>
        </div>
        """
        
        return html
    
    def action_back_to_preview(self):
        """Volta para o preview"""
        self.ensure_one()
        self.state = 'preview'
        self.progress_percentage = 30
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'bank.statement.import.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': self.env.context,
        }
    
    def action_back_to_upload(self):
        """Volta para upload"""
        self.ensure_one()
        self.state = 'upload'
        self.progress_percentage = 0
        self.processed_data = False
        self.preview_data = False
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'bank.statement.import.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': self.env.context,
        }
    
    def action_go_to_accounting(self):
        """Vai para o dashboard de contabilidade"""
        return {
            'type': 'ir.actions.act_url',
            'url': '/odoo/accounting',
            'target': 'self',
        }
    
    def action_cancel(self):
        """Cancela o wizard"""
        return {'type': 'ir.actions.act_window_close'}
    
    def _convert_to_float(self, value):
        """Converte valor moçambicano para float"""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Remove currency symbol (MZN, MT, etc) and clean the string
            value = value.upper().replace('MZN', '').replace('MT', '').strip()
            # Remove + or - prefix but keep track of sign
            is_negative = value.startswith('-')
            value = value.replace('+', '').replace('-', '')
            # Remove espaços e converte formato moçambicano
            value = value.replace(' ', '').replace('.', '').replace(',', '.')
            try:
                result = float(value)
                return -result if is_negative else result
            except:
                return 0.0
        return 0.0