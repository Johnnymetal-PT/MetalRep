from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    # IMPORTANTE: Este módulo adiciona funcionalidade de plano de contas personalizado
    # mantendo compatibilidade com o sistema padrão do Odoo.
    
    # Campo auto-incrementado para ordem
    accg_nr_order = fields.Integer(
        string='Número de Ordem',
        readonly=True,
        copy=False,
        help='Número sequencial único para ordem'
    )
    
    # Campos separados para numeração de clientes e fornecedores
    accg_nr_order_customer = fields.Integer(
        string='Número de Ordem Cliente',
        readonly=True,
        copy=False,
        help='Número sequencial para clientes (começa de 1)'
    )
    
    accg_nr_order_supplier = fields.Integer(
        string='Número de Ordem Fornecedor',
        readonly=True,
        copy=False,
        help='Número sequencial para fornecedores (começa de 1)'
    )
    
    # Torna o campo country_id obrigatório
    country_id = fields.Many2one(
        'res.country',
        string='País',
        required=True,
        help='País é obrigatório para todos os parceiros'
    )
    
    # Campo para armazenar as contas criadas dinamicamente para este parceiro
    dynamic_account_ids = fields.One2many(
        'account.account',
        'partner_id',
        string='Contas Dinâmicas',
        domain=[('partner_generated', '=', True)],
        help='Contas contábeis criadas automaticamente para este parceiro'
    )
    
    # Campo company_id já existe no modelo base, vamos apenas torná-lo obrigatório via constraint
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create para gerar número sequencial, garantir company_id, country_id e desabilitar contas contábeis automáticas"""
        
        # Detectar se estamos em contexto de importação
        is_import = self.env.context.get('import_file', False) or \
                   'import' in str(self.env.context.get('active_model', '')) or \
                   'import' in str(self.env.context)
        
        if is_import:
            _logger.info(f"[IMPORTAÇÃO DETECTADA] Processando {len(vals_list)} registros")
            _logger.info(f"[IMPORTAÇÃO] Contexto: {self.env.context}")
            
            # Detectar tipo de importação pelo contexto
            import_type = 'general'
            context_str = str(self.env.context).lower()
            active_model = self.env.context.get('active_model', '')
            
            # Verificar se está importando de uma view específica
            if 'customer' in context_str or active_model == 'res.partner.customer':
                import_type = 'customer'
                _logger.info("[IMPORTAÇÃO] Tipo detectado: CLIENTE")
            elif 'supplier' in context_str or 'vendor' in context_str or active_model == 'res.partner.supplier':
                import_type = 'supplier'
                _logger.info("[IMPORTAÇÃO] Tipo detectado: FORNECEDOR")
            
            # Se todos os registros não têm rank definido, definir baseado no tipo de importação
            all_without_rank = all(
                vals.get('customer_rank', 0) == 0 and vals.get('supplier_rank', 0) == 0 
                for vals in vals_list
            )
            
            if all_without_rank:
                _logger.info(f"[IMPORTAÇÃO] Todos registros sem rank. Aplicando tipo: {import_type}")
                for vals in vals_list:
                    if import_type == 'customer':
                        vals['customer_rank'] = 1
                    elif import_type == 'supplier':
                        vals['supplier_rank'] = 1
            
            # Obter próximos números para cada tipo
            self._cr.execute("""
                SELECT 
                    COALESCE(MAX(accg_nr_order), 0) as max_general,
                    COALESCE(MAX(accg_nr_order_customer), 0) as max_customer,
                    COALESCE(MAX(accg_nr_order_supplier), 0) as max_supplier
                FROM res_partner
            """)
            result = self._cr.fetchone()
            next_general = (result[0] if result else 0) + 1
            next_customer = (result[1] if result else 0) + 1
            next_supplier = (result[2] if result else 0) + 1
            
            _logger.info(f"[IMPORTAÇÃO] Próximos números - Geral: {next_general}, Cliente: {next_customer}, Fornecedor: {next_supplier}")
        
        # Converter para lista se for único dict
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        
        for vals in vals_list:
            # Garante que company_id está presente
            if not vals.get('company_id'):
                vals['company_id'] = self.env.company.id
                
            # Garante que country_id está presente
            if not vals.get('country_id'):
                company_country = self.env.company.country_id
                if company_country:
                    vals['country_id'] = company_country.id
                else:
                    mozambique = self.env['res.country'].search([('code', '=', 'MZ')], limit=1)
                    if mozambique:
                        vals['country_id'] = mozambique.id
            
            # Determinar se é cliente ou fornecedor
            # IMPORTANTE: Durante importação, customer_rank pode vir 0 mas ainda ser cliente
            # Verificar também is_company e contexto
            customer_rank = vals.get('customer_rank', 0)
            supplier_rank = vals.get('supplier_rank', 0)
            
            # Se não tem rank definido mas está sendo importado como cliente/fornecedor
            if is_import and customer_rank == 0 and supplier_rank == 0:
                # Verificar contexto da importação
                import_context = str(self.env.context)
                if 'customer' in import_context.lower():
                    customer_rank = 1
                    vals['customer_rank'] = 1
                    _logger.info(f"[IMPORTAÇÃO] Definindo customer_rank=1 para '{vals.get('name')}' baseado no contexto")
                elif 'supplier' in import_context.lower() or 'vendor' in import_context.lower():
                    supplier_rank = 1
                    vals['supplier_rank'] = 1
                    _logger.info(f"[IMPORTAÇÃO] Definindo supplier_rank=1 para '{vals.get('name')}' baseado no contexto")
                # Se é empresa, assumir que é cliente
                elif vals.get('is_company', False):
                    customer_rank = 1
                    vals['customer_rank'] = 1
                    _logger.info(f"[IMPORTAÇÃO] Definindo customer_rank=1 para empresa '{vals.get('name')}'")
            
            is_customer = customer_rank > 0
            is_supplier = supplier_rank > 0
            
            if is_import:
                # Em importação, usar numeração sequencial pré-calculada
                if is_customer and not vals.get('accg_nr_order_customer'):
                    vals['accg_nr_order_customer'] = next_customer
                    vals['accg_nr_order'] = next_customer
                    _logger.info(f"[IMPORTAÇÃO] Cliente '{vals.get('name')}' recebe número: {next_customer}")
                    next_customer += 1
                
                if is_supplier and not vals.get('accg_nr_order_supplier'):
                    vals['accg_nr_order_supplier'] = next_supplier
                    if not is_customer:  # Se for só fornecedor
                        vals['accg_nr_order'] = next_supplier
                    _logger.info(f"[IMPORTAÇÃO] Fornecedor '{vals.get('name')}' recebe número: {next_supplier}")
                    next_supplier += 1
                
                # Se não for nem cliente nem fornecedor, usar geral
                if not is_customer and not is_supplier and not vals.get('accg_nr_order'):
                    vals['accg_nr_order'] = next_general
                    next_general += 1
            else:
                # Criação individual (não importação) - lógica original
                if is_customer and not vals.get('accg_nr_order_customer'):
                    self._cr.execute("""
                        SELECT COALESCE(MAX(accg_nr_order_customer), 0) as max_order
                        FROM res_partner
                        WHERE accg_nr_order_customer IS NOT NULL
                    """)
                    result = self._cr.fetchone()
                    max_value = result[0] if result else 0
                    vals['accg_nr_order_customer'] = max_value + 1
                    _logger.info(f"Gerando accg_nr_order_customer: {vals['accg_nr_order_customer']}")
                
                if is_supplier and not vals.get('accg_nr_order_supplier'):
                    self._cr.execute("""
                        SELECT COALESCE(MAX(accg_nr_order_supplier), 0) as max_order
                        FROM res_partner
                        WHERE accg_nr_order_supplier IS NOT NULL
                    """)
                    result = self._cr.fetchone()
                    max_value = result[0] if result else 0
                    vals['accg_nr_order_supplier'] = max_value + 1
                    _logger.info(f"Gerando accg_nr_order_supplier: {vals['accg_nr_order_supplier']}")
                
                # Manter accg_nr_order original para compatibilidade
                if not vals.get('accg_nr_order'):
                    if is_customer and not is_supplier:
                        vals['accg_nr_order'] = vals.get('accg_nr_order_customer', 0)
                    elif is_supplier and not is_customer:
                        vals['accg_nr_order'] = vals.get('accg_nr_order_supplier', 0)
                    else:
                        self._cr.execute("""
                            SELECT COALESCE(MAX(accg_nr_order), 0) as max_order
                            FROM res_partner
                            WHERE accg_nr_order IS NOT NULL
                        """)
                        result = self._cr.fetchone()
                        max_value = result[0] if result else 0
                        vals['accg_nr_order'] = max_value + 1
                        _logger.info(f"Gerando accg_nr_order geral: {vals['accg_nr_order']}")
        
        # Criar todos os parceiros
        partners = super().create(vals_list)
        
        # Criar planos de contas dinâmicos para cada parceiro
        for partner in partners:
            partner._create_dynamic_accounts()
        
        if is_import:
            _logger.info(f"[IMPORTAÇÃO CONCLUÍDA] {len(partners)} parceiros criados com numeração automática")
        
        return partners
    
    def write(self, vals):
        """Override write para garantir company_id, country_id e desabilitar contas contábeis automáticas"""
        # Se estiver tentando limpar company_id, impede
        if 'company_id' in vals and not vals['company_id']:
            raise ValidationError('O campo Empresa é obrigatório e não pode ser removido.')
        
        # Se estiver tentando limpar country_id, impede
        if 'country_id' in vals and not vals['country_id']:
            raise ValidationError('O campo País é obrigatório e não pode ser removido.')
        
        return super().write(vals)
    
    # def unlink(self):
    #     """Override unlink para impedir exclusão de contatos"""
    #     if self:
    #         raise ValidationError(
    #             '⛔ OPERAÇÃO NÃO PERMITIDA\n'
    #             '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n'
    #             '❌ A exclusão de contatos está bloqueada por política de segurança.\n\n'
    #             '📋 MOTIVOS:\n'
    #             '   • Preservação do histórico de transações\n'
    #             '   • Manutenção da integridade referencial\n'
    #             '   • Conformidade com requisitos de auditoria\n'
    #             '   • Rastreabilidade de operações comerciais\n\n'
    #             '✅ ALTERNATIVA RECOMENDADA:\n'
    #             '   → Use a opção "Arquivar" para ocultar contatos inativos\n'
    #             '   → Acesse: Ação > Arquivar\n\n'
    #             '💡 Contatos arquivados:\n'
    #             '   • Não aparecem em pesquisas e listas\n'
    #             '   • Mantêm todo o histórico preservado\n'
    #             '   • Podem ser desarquivados quando necessário\n'
    #             '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
    #         )
    #     return super().unlink()
    
    @api.constrains('company_id')
    def _check_company_id(self):
        """Validação para garantir que company_id sempre existe"""
        for partner in self:
            if not partner.company_id:
                raise ValidationError('O campo Empresa é obrigatório.')
    
    @api.constrains('country_id')
    def _check_country_id(self):
        """Validação para garantir que country_id sempre existe"""
        for partner in self:
            if not partner.country_id:
                raise ValidationError('O campo País é obrigatório.')
    
    @api.model
    def _recompute_accg_nr_order(self):
        """
        Método utilitário para recalcular accg_nr_order para todos os parceiros.
        Útil para corrigir dados após importações ou migrações.
        Pode ser executado via Server Action ou script.
        """
        # Buscar parceiros sem accg_nr_order ou com valor NULL/0
        self._cr.execute("""
            SELECT id FROM res_partner
            WHERE accg_nr_order IS NULL OR accg_nr_order = 0
            ORDER BY id
        """)
        partner_ids = [row[0] for row in self._cr.fetchall()]
        
        if not partner_ids:
            _logger.info("Todos os parceiros já têm accg_nr_order definido.")
            return True
        
        # Pegar o maior valor existente
        self._cr.execute("""
            SELECT COALESCE(MAX(accg_nr_order), 0) as max_order
            FROM res_partner
            WHERE accg_nr_order IS NOT NULL AND accg_nr_order > 0
        """)
        result = self._cr.fetchone()
        counter = (result[0] if result else 0) + 1
        
        # Atualizar parceiros sem accg_nr_order
        for partner_id in partner_ids:
            self._cr.execute("""
                UPDATE res_partner
                SET accg_nr_order = %s
                WHERE id = %s
            """, (counter, partner_id))
            _logger.info(f"Atribuído accg_nr_order={counter} para parceiro ID={partner_id}")
            counter += 1
        
        self._cr.commit()
        _logger.info(f"Processo concluído: {len(partner_ids)} parceiros atualizados.")
        
        return True
    
    @api.model
    def fix_duplicate_accg_nr_order(self):
        """
        Corrige possíveis duplicações de accg_nr_order.
        Útil após importações ou problemas de concorrência.
        """
        # Encontrar valores duplicados
        self._cr.execute("""
            SELECT accg_nr_order, COUNT(*) as count
            FROM res_partner
            WHERE accg_nr_order IS NOT NULL
            GROUP BY accg_nr_order
            HAVING COUNT(*) > 1
        """)
        duplicates = self._cr.fetchall()
        
        if not duplicates:
            _logger.info("Nenhuma duplicação encontrada em accg_nr_order.")
            return True
        
        # Pegar o maior valor existente
        self._cr.execute("""
            SELECT COALESCE(MAX(accg_nr_order), 0) as max_order
            FROM res_partner
            WHERE accg_nr_order IS NOT NULL
        """)
        result = self._cr.fetchone()
        counter = (result[0] if result else 0) + 1
        
        # Corrigir duplicações
        for dup_value, count in duplicates:
            # Pegar todos os parceiros com esse valor duplicado (exceto o primeiro)
            self._cr.execute("""
                SELECT id FROM res_partner
                WHERE accg_nr_order = %s
                ORDER BY id
                OFFSET 1
            """, (dup_value,))
            partner_ids = [row[0] for row in self._cr.fetchall()]
            
            # Atribuir novos valores únicos
            for partner_id in partner_ids:
                self._cr.execute("""
                    UPDATE res_partner
                    SET accg_nr_order = %s
                    WHERE id = %s
                """, (counter, partner_id))
                _logger.info(f"Corrigido duplicação: parceiro ID={partner_id} novo accg_nr_order={counter}")
                counter += 1
        
        self._cr.commit()
        _logger.info(f"Correção concluída: {len(duplicates)} duplicações resolvidas.")
        
        return True
    
    def _create_dynamic_accounts(self):
        """
        Cria planos de contas dinâmicos baseados nas configurações da empresa.
        
        Lógica inteligente:
        - Contas 'asset_receivable' são atribuídas a property_account_receivable_id SE é cliente
        - Contas 'liability_payable' são atribuídas a property_account_payable_id SE é fornecedor
        - Outros tipos de contas são sempre criados como contas dinâmicas
        - Evita duplicação: contas nos campos padrão não aparecem nas dinâmicas
        """
        self.ensure_one()
        
        # Buscar configurações de plano de contas da empresa
        chart_configs = self.company_id.chart_account_ids
        
        if not chart_configs:
            return  # Sem configurações, não cria contas
        
        # Determinar tipo de parceiro baseado em customer_rank e supplier_rank
        is_customer = self.customer_rank > 0
        is_supplier = self.supplier_rank > 0
        
        # Separar configurações por tipo
        receivable_configs = chart_configs.filtered(lambda c: c.account_type == 'asset_receivable')
        payable_configs = chart_configs.filtered(lambda c: c.account_type == 'liability_payable')
        
        # Separar contas de adiantamento
        # NOTA: A lógica está baseada no prefixo
        # 419 = adiantamento cliente, 429 = adiantamento fornecedor
        # Não depende do campo adiantamento pois pode estar incorreto no banco
        advance_customer_configs = chart_configs.filtered(
            lambda c: c.prefix == '419'
        )
        advance_supplier_configs = chart_configs.filtered(
            lambda c: c.prefix == '429'
        )
        
        # Outras contas (excluindo receivable, payable e adiantamentos)
        other_configs = chart_configs.filtered(
            lambda c: c.account_type not in ('asset_receivable', 'liability_payable')
            and c.prefix not in ('419', '429')
        )
        
        # Processar contas receivable APENAS se for cliente
        if receivable_configs and is_customer:
            # Primeira config vai para campo padrão
            config = receivable_configs[0]
            account = self._create_account_from_config(config, for_standard_field=True)
            if account:
                self.property_account_receivable_id = account
                # Configs extras vão para dinâmicas
                for extra_config in receivable_configs[1:]:
                    self._create_account_from_config(extra_config, for_standard_field=False)
        # Se não é cliente, NÃO criar contas receivable
        
        # Processar contas payable APENAS se for fornecedor
        if payable_configs and is_supplier:
            # Primeira config vai para campo padrão
            config = payable_configs[0]
            account = self._create_account_from_config(config, for_standard_field=True)
            if account:
                self.property_account_payable_id = account
                # Configs extras vão para dinâmicas
                for extra_config in payable_configs[1:]:
                    self._create_account_from_config(extra_config, for_standard_field=False)
        # Se não é fornecedor, NÃO criar contas payable
        
        # Processar outros tipos de contas (sempre como dinâmicas)
        for config in other_configs:
            self._create_account_from_config(config, for_standard_field=False)
        
        # Processar contas de adiantamento de CLIENTE apenas se for cliente
        if advance_customer_configs and is_customer:
            for config in advance_customer_configs:
                self._create_account_from_config(config, for_standard_field=False)
        
        # Processar contas de adiantamento de FORNECEDOR apenas se for fornecedor
        if advance_supplier_configs and is_supplier:
            for config in advance_supplier_configs:
                self._create_account_from_config(config, for_standard_field=False)
    
    def _create_account_from_config(self, config, for_standard_field=False):
        """
        Cria uma conta baseada na configuração fornecida.
        
        Args:
            config: Configuração do plano de contas
            for_standard_field: Se True, conta é para campo padrão (não aparece em dinâmicas)
                               Se False, conta é dinâmica (aparece em dinâmicas)
        
        Returns:
            Conta criada ou existente
        """
        # Gerar código da conta usando a fórmula
        account_code = self._generate_account_code(config)
        
        # Verificar se conta com este código já existe
        existing_account = self.env['account.account'].search([
            ('code', '=', account_code)
        ], limit=1)
        
        if existing_account:
            return existing_account  # Retornar conta existente
        
        # Preparar valores para criar a conta
        account_vals = self._prepare_account_vals(config, account_code)
        
        # Se for para campo padrão, NÃO associar partner_id (evita duplicação)
        if for_standard_field:
            account_vals.pop('partner_id', None)
            account_vals.pop('partner_generated', None)
        
        # Criar e retornar a conta
        return self.env['account.account'].create(account_vals)
    
    def _generate_account_code(self, config):
        """
        Gera o código da conta usando a fórmula:
        PREFIX + PAÍS + ZEROS + ACCG_NR_ORDER
        
        Exemplo: 411 + 1 + 0043 = 4110043
        """
        # PREFIX do config
        prefix = config.prefix or ''
        
        # PAÍS (1 se mesmo país, 2 se diferente)
        # Opção: usar código especial "9" para contas de adiantamento
        # if config.adiantamento:
        #     country_code = "9"  # Código especial para adiantamentos
        # else:
        if self.country_id and self.company_id.country_id:
            country_code = "1" if self.country_id.id == self.company_id.country_id.id else "2"
        else:
            country_code = "1"  # Default se não houver país definido
        
        # ZEROS + ACCG_NR_ORDER
        # partner_limite define quantos dígitos terá o número
        zeros_count = int(config.partner_limite) if config.partner_limite > 0 else 4
        
        # Usar o campo apropriado baseado no tipo
        if self.customer_rank > 0 and self.supplier_rank == 0:
            # Cliente puro - usar accg_nr_order_customer
            order_number = self.accg_nr_order_customer or self.accg_nr_order or 1
        elif self.supplier_rank > 0 and self.customer_rank == 0:
            # Fornecedor puro - usar accg_nr_order_supplier
            order_number = self.accg_nr_order_supplier or self.accg_nr_order or 1
        else:
            # Outros casos - usar accg_nr_order
            order_number = self.accg_nr_order or 1
            
        padded_order = str(order_number).zfill(zeros_count)
        
        # Montar código final
        return f"{prefix}{country_code}{padded_order}"
    
    def _prepare_account_vals(self, config, account_code):
        """
        Prepara os valores para criar a conta em account.account
        mapeando os campos de company.chart.account
        """
        
        advance_type = False
        if config.adiantamento:
            if config.account_type == 'asset_receivable':
                    advance_type = 'customer'
            elif config.account_type == 'liability_payable':
                    advance_type = 'supplier'
        # Mapear campos de company.chart.account para account.account
        vals = {
            'code': account_code,
            'name': f"{config.name} - {self.name}",  # Nome da conta + nome do parceiro
            'account_type': config.account_type,
            'reconcile': config.reconcile,
            
            # Vincular ao parceiro
            'partner_id': self.id,
            'partner_generated': True,
            
            'is_advance_account': config.adiantamento,
            'advance_type': advance_type,
            
            # Campos opcionais
            'currency_id': config.currency_id.id if config.currency_id else False,
            'non_trade': config.non_trade,
            'deprecated': config.deprecated,
            
            # Tags (Many2many)
            'tag_ids': [(6, 0, config.tag_ids.ids)] if config.tag_ids else False,
            
            # Diários permitidos (Many2many)
            'allowed_journal_ids': [(6, 0, config.allowed_journal_ids.ids)] if config.allowed_journal_ids else False,
        }
        
        # Adicionar grupo se existir
        if config.group_id:
            vals['group_id'] = config.group_id.id
        
        
        return vals