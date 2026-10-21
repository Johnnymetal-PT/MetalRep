# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import timedelta
from odoo.tools.misc import format_date, formatLang

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Supplier follow-up specific fields
    supplier_followup_line_id = fields.Many2one(
        'account_followup.followup.line',
        string='Nível de Follow-up de Fornecedor',
        copy=False,
        company_dependent=True,
        help="O nível de follow-up atual para pagamentos a fornecedores"
    )
    
    supplier_followup_next_action_date = fields.Date(
        string='Próxima Data de Ação de Fornecedor',
        copy=False,
        company_dependent=True,
        help="A próxima data planeada para ações de follow-up de pagamentos a fornecedores"
    )
    
    supplier_followup_responsible_id = fields.Many2one(
        'res.users',
        string='Responsável pelo Follow-up de Fornecedor',
        help="Utilizador responsável pelos follow-ups de pagamento a fornecedores",
        tracking=True,
        copy=False,
        company_dependent=True,
    )
    
    supplier_followup_status = fields.Selection(
        [('no_action_needed', 'Sem Ação Necessária'),
         ('with_overdue_bills', 'Com Faturas em Atraso'),
         ('in_need_of_action', 'Necessita de Ação')],
        string='Estado do Follow-up de Fornecedor',
        compute='_compute_supplier_followup_status',
        search='_search_supplier_followup_status',
        store=False,
        groups='account.group_account_readonly,account.group_account_invoice',
    )
    
    supplier_followup_reminder_type = fields.Selection(
        [('automatic', 'Automatic'),
         ('manual', 'Manual')],
        string='Tipo de Lembrete de Fornecedor',
        default='manual',
        company_dependent=True,
        help="Como os lembretes de pagamento a fornecedores devem ser geridos"
    )
    
    unpaid_bills_count = fields.Integer(
        string="Faturas por Pagar",
        compute='_compute_unpaid_bills'
    )
    
    total_due_supplier = fields.Monetary(
        string='Total a Pagar a Fornecedores',
        compute='_compute_supplier_totals'
    )
    
    total_overdue_supplier = fields.Monetary(
        string='Total em Atraso a Fornecedores',
        compute='_compute_supplier_totals'
    )
    
    unreconciled_supplier_aml_ids = fields.One2many(
        'account.move.line',
        compute='_compute_unreconciled_supplier_aml_ids',
        string='Lançamentos de Fornecedor por Conciliar'
    )

    @api.depends('unreconciled_supplier_aml_ids')
    def _compute_supplier_followup_status(self):
        today = fields.Date.context_today(self)
        for partner in self:
            if not partner.unreconciled_supplier_aml_ids:
                partner.supplier_followup_status = 'no_action_needed'
            else:
                has_overdue = any(
                    (aml.date_maturity or aml.date) < today
                    for aml in partner.unreconciled_supplier_aml_ids
                )
                
                if not has_overdue:
                    partner.supplier_followup_status = 'no_action_needed'
                elif partner.supplier_followup_next_action_date and partner.supplier_followup_next_action_date <= today:
                    partner.supplier_followup_status = 'in_need_of_action'
                else:
                    partner.supplier_followup_status = 'with_overdue_bills'

    def _search_supplier_followup_status(self, operator, value):
        """Allow searching partners by supplier follow-up status"""
        if isinstance(value, str):
            value = [value]
        if operator not in ('in', '=', '!=') or not value:
            return []
        
        value = [v for v in value if v in ['in_need_of_action', 'with_overdue_bills', 'no_action_needed']]
        
        # Get all partners with supplier transactions
        all_partners = self.search([('supplier_rank', '>', 0)])
        
        # Filter based on status
        partner_ids = []
        today = fields.Date.context_today(self)
        
        for partner in all_partners:
            has_overdue = False
            if partner.unreconciled_supplier_aml_ids:
                for aml in partner.unreconciled_supplier_aml_ids:
                    if (aml.date_maturity or aml.date) < today:
                        has_overdue = True
                        break
            
            status = 'no_action_needed'
            if has_overdue:
                if partner.supplier_followup_next_action_date and partner.supplier_followup_next_action_date <= today:
                    status = 'in_need_of_action'
                else:
                    status = 'with_overdue_bills'
            
            if operator == '=' and status in value:
                partner_ids.append(partner.id)
            elif operator == 'in' and status in value:
                partner_ids.append(partner.id)
            elif operator == '!=' and status not in value:
                partner_ids.append(partner.id)
        
        return [('id', 'in', partner_ids)]

    def get_formatted_supplier_amounts(self):
        """Helper method to get formatted amounts for email templates"""
        self.ensure_one()

        return {
            'total_due_formatted': formatLang(self.env, self.total_due_supplier, currency_obj=self.currency_id),
            'total_overdue_formatted': formatLang(self.env, self.total_overdue_supplier, currency_obj=self.currency_id),
        }
    
    @api.depends('unreconciled_supplier_aml_ids')
    def _compute_unpaid_bills(self):
        for partner in self:
            bills = partner.unreconciled_supplier_aml_ids.move_id.filtered(
                lambda m: m.move_type in ('in_invoice', 'in_refund')
            )
            partner.unpaid_bills_count = len(bills)

    @api.depends('unreconciled_supplier_aml_ids')
    def _compute_supplier_totals(self):
        today = fields.Date.context_today(self)
        for partner in self:
            total_due = 0.0
            total_overdue = 0.0
            
            for aml in partner.unreconciled_supplier_aml_ids:
                amount = abs(aml.amount_residual_currency if aml.currency_id else aml.amount_residual)
                total_due += amount
                
                if (aml.date_maturity or aml.date) < today:
                    total_overdue += amount
            
            partner.total_due_supplier = total_due
            partner.total_overdue_supplier = total_overdue

    def _compute_unreconciled_supplier_aml_ids(self):
        # Um utilizador sem acesso de leitura a contabilidade — por exemplo quem
        # so consulta contactos — nao pode pesquisar account.move.line. Sem esta
        # guarda, abrir uma ficha de contacto rebenta com AccessError, porque
        # supplier_followup_status depende deste campo.
        # O campo fica vazio, que e' a leitura correcta para quem nao ve o razao
        # de fornecedores: nao se expoem linhas que o utilizador nao pode ler.
        if not self.env['account.move.line'].has_access('read'):
            for partner in self:
                partner.unreconciled_supplier_aml_ids = self.env['account.move.line']
            return
        for partner in self:
            partner.unreconciled_supplier_aml_ids = self.env['account.move.line'].search([
                ('reconciled', '=', False),
                ('account_id.account_type', '=', 'liability_payable'),
                ('parent_state', '=', 'posted'),
                ('partner_id', '=', partner.id),
                ('company_id', 'child_of', self.env.company.id),
            ])

    def action_view_unpaid_bills(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_in_invoice_type")
        
        bill_ids = self.unreconciled_supplier_aml_ids.move_id.filtered(
            lambda m: m.move_type in ('in_invoice', 'in_refund')
        ).ids
        
        action['domain'] = [('id', 'in', bill_ids)]
        action['context'] = {
            'default_move_type': 'in_invoice',
            'default_partner_id': self.id,
        }
        return action
    
    def execute_supplier_followup(self, options):
        """ Execute the actions to do with supplier follow-ups for this partner.
        This is called when processing the supplier follow-ups manually, via the wizard.
        """
        self.ensure_one()
        to_print = self._execute_supplier_followup_partner(options=options)
        if options.get('print') and to_print:
            return self.env['supplier.followup.report']._print_supplier_followup_letter(self, options)
    
    def _execute_supplier_followup_partner(self, options):
        """ Execute the supplier followup actions for this partner
        Returns True if the followup was executed, False otherwise
        """
        self.ensure_one()
        
        # Update partner followup information
        if options.get('followup_line_id'):
            self.supplier_followup_line_id = self.browse(options['followup_line_id'])
        
        if options.get('next_action_date'):
            self.supplier_followup_next_action_date = options['next_action_date']
        
        # Send email if requested
        if options.get('email'):
            self.env['supplier.followup.report']._send_email(options)
            
            # Create an email activity to track that we sent the followup
            mail_activity_type = self.env.ref('mail.mail_activity_data_email', raise_if_not_found=False)
            if mail_activity_type:
                self.activity_schedule(
                    activity_type_id=mail_activity_type.id,
                    summary=_('Email de Follow-up de Pagamento a Fornecedor Enviado'),
                    note=options.get('body', _('Email de follow-up enviado para pagamentos a fornecedores')),
                    user_id=(self.supplier_followup_responsible_id or self.env.user).id,
                )
        
        # Send SMS if requested  
        if options.get('sms'):
            self.env['supplier.followup.report']._send_sms(options)
        
        # Create activity if requested
        if options.get('create_activity'):
            activity_type_id = options.get('activity_type_id')
            if not activity_type_id:
                activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
                activity_type_id = activity_type.id if activity_type else False
            
            if activity_type_id:
                self.env['mail.activity'].create({
                    'res_id': self.id,
                    'res_model_id': self.env['ir.model']._get('res.partner').id,
                    'activity_type_id': activity_type_id,
                    'summary': options.get('activity_summary', _('Follow-up de Pagamento a Fornecedor')),
                    'note': options.get('body', ''),
                    'date_deadline': options.get('activity_date_deadline', fields.Date.today()),
                    'user_id': self.supplier_followup_responsible_id.id or self.env.user.id,
                })
        
        # Post message in chatter
        recipient_ids = options.get('email_recipient_ids', [])
        if recipient_ids and hasattr(recipient_ids, 'ids'):
            recipient_ids = recipient_ids.ids
        elif recipient_ids and not isinstance(recipient_ids, list):
            recipient_ids = [recipient_ids]
        
        self.message_post(
            body=_('Follow-up de pagamento a fornecedor processado'),
            partner_ids=recipient_ids,
        )
        
        return True

    def action_supplier_followup_reconcile(self):
        """Open reconciliation view for supplier bills"""
        self.ensure_one()
        import ast
        
        # Use the same action as account_followup
        action_values = self.env["ir.actions.actions"]._for_xml_id("account_accountant.action_move_line_posted_unreconciled")
        
        # Parse existing domain and add partner filter
        domain = ast.literal_eval(action_values.get('domain', '[]'))
        domain.append(('partner_id', '=', self.id))
        
        # Filter for payable accounts (supplier transactions)
        domain.append(('account_type', '=', 'liability_payable'))
        
        action_values['domain'] = domain
        
        # Parse context if it's a string, otherwise use as dict
        context = action_values.get('context', {})
        if isinstance(context, str):
            context = ast.literal_eval(context)
        
        context.update({
            'default_partner_id': self.id,
            'search_default_unreconciled': 1,
        })
        
        action_values['context'] = context
        
        return action_values

    def _execute_supplier_followup_line(self, followup_line):
        """Execute follow-up actions for supplier payments"""
        self.ensure_one()
        
        # Update follow-up level on move lines
        for aml in self.unreconciled_supplier_aml_ids:
            if not aml.supplier_followup_line_id or \
               aml.supplier_followup_line_id.delay < followup_line.delay:
                aml.supplier_followup_line_id = followup_line
        
        # Update partner follow-up info
        self.supplier_followup_line_id = followup_line
        
        # Calculate next action date
        if followup_line:
            next_followup_lines = self.env['account_followup.followup.line'].search([
                ('company_id', '=', self.env.company.id),
                ('delay', '>', followup_line.delay)
            ], order='delay asc', limit=1)
            
            if next_followup_lines:
                today = fields.Date.context_today(self)
                self.supplier_followup_next_action_date = today + timedelta(
                    days=next_followup_lines.delay - followup_line.delay
                )
        
        # Create activity if configured
        if followup_line.create_activity:
            self._create_supplier_followup_activity(followup_line)
        
        # Send email if configured (internal notification)
        if followup_line.send_email:
            self._send_supplier_followup_email(followup_line)
    
    def _create_supplier_followup_activity(self, followup_line):
        """Create an activity for supplier payment follow-up"""
        self.ensure_one()
        
        responsible = self._get_supplier_followup_responsible(followup_line)
        if not responsible:
            responsible = self.env.user
        
        activity_data = {
            'res_id': self.id,
            'res_model_id': self.env['ir.model']._get('res.partner').id,
            'activity_type_id': followup_line.activity_type_id.id or self.env.ref('mail.mail_activity_data_todo').id,
            'summary': followup_line.activity_summary or _('Follow-up de Pagamento a Fornecedor'),
            'note': followup_line.activity_note or _('Pagamento necessário para faturas de %s') % self.name,
            'date_deadline': fields.Date.context_today(self),
            'user_id': responsible.id,
        }
        
        self.env['mail.activity'].create(activity_data)
    
    def _get_supplier_followup_responsible(self, followup_line):
        """Get the responsible user for supplier follow-up"""
        self.ensure_one()
        
        if self.supplier_followup_responsible_id:
            return self.supplier_followup_responsible_id
        
        # Default to AP manager or current user
        return self.user_id or self.env.user
    
    def _send_supplier_followup_email(self, followup_line):
        """Send internal email notification for supplier payments"""
        self.ensure_one()
        
        if not followup_line.mail_template_id:
            # Create a basic notification
            subject = _('Lembrete de Pagamento: Faturas de %s') % self.name
            body = _("""
                <p>Este é um lembrete de que temos faturas em atraso de <b>%s</b>.</p>
                <p>Total em Dívida: %s</p>
                <p>Total em Atraso: %s</p>
                <p>Por favor, reveja e processe os pagamentos.</p>
            """) % (
                self.name,
                formatLang(self.env, self.total_due_supplier, currency_obj=self.currency_id),
                formatLang(self.env, self.total_overdue_supplier, currency_obj=self.currency_id)
            )
            
            mail_values = {
                'subject': subject,
                'body_html': body,
                'email_to': self._get_supplier_followup_responsible(followup_line).email,
                'email_from': self.env.company.email or self.env.user.email,
            }
            
            self.env['mail.mail'].create(mail_values).send()
        else:
            # Use the template
            followup_line.mail_template_id.send_mail(self.id)
    
