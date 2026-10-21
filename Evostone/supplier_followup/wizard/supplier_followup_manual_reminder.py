# -*- coding: utf-8 -*-
from odoo import api, fields, models, Command, _
from odoo.tools.misc import formatLang

class SupplierFollowupManualReminder(models.TransientModel):
    _name = 'supplier.followup.manual.reminder'
    _inherit = 'mail.composer.mixin'
    _description = "Wizard for processing supplier payment reminders"

    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        assert self.env.context['active_model'] == 'res.partner'
        partner = self.env['res.partner'].browse(self.env.context['active_ids'])
        partner.ensure_one()
        
        followup_line = partner.supplier_followup_line_id
        
        # Tenta obter o template padrão interno para AP team
        default_email_template = False
        try:
            default_email_template = self.env.ref('supplier_followup.email_template_supplier_payment_reminder_internal')
        except:
            pass
        
        if followup_line:
            # Para email: usa supplier_mail_template_id se existir, senão usa o template interno
            email_template = followup_line.supplier_mail_template_id or default_email_template
            # Para SMS: usa supplier_sms_template_id se existir, senão usa o padrão
            sms_template = followup_line.supplier_sms_template_id or followup_line.sms_template_id
            
            defaults.update(
                email=followup_line.send_email,
                sms=followup_line.send_sms,
                template_id=email_template.id if email_template else False,
                sms_template_id=sms_template.id if sms_template else False,
                create_activity=followup_line.create_activity,
            )
        else:
            # Se não há followup_line, usa o template padrão interno para AP team
            if default_email_template:
                defaults['template_id'] = default_email_template.id
        
        # Get list of unpaid bills
        bills = partner.unreconciled_supplier_aml_ids.move_id.filtered(
            lambda m: m.move_type in ('in_invoice', 'in_refund')
        )
        
        defaults.update(
            partner_id=partner.id,
            company_id=self.env.company.id,
            attachment_ids=[Command.set(bills.message_main_attachment_id.ids)],
            render_model='res.partner',
            followup_line_id=followup_line.id if followup_line else False,
        )
        return defaults

    partner_id = fields.Many2one(comodel_name='res.partner', string='Supplier', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    followup_line_id = fields.Many2one('account_followup.followup.line', string='Follow-up Level')
    
    # Email fields
    email = fields.Boolean(string='Send Email')
    email_recipient_ids = fields.Many2many(
        string="Email Recipients", 
        comodel_name='res.partner',
        compute='_compute_email_recipient_ids', 
        store=True, 
        readonly=False,
        relation='rel_supplier_followup_manual_reminder_res_partner'
    )
    
    # SMS fields
    sms = fields.Boolean(string='Send SMS')
    sms_body = fields.Char(compute='_compute_sms_body', readonly=False, store=True)
    sms_template_id = fields.Many2one(comodel_name='sms.template', domain=[('model', '=', 'res.partner')])
    
    # Print fields
    print = fields.Boolean(default=True, string='Print Report')
    
    # Activity fields
    create_activity = fields.Boolean(string='Schedule Activity')
    activity_type_id = fields.Many2one('mail.activity.type', string='Activity Type')
    activity_summary = fields.Char(string='Activity Summary')
    activity_date_deadline = fields.Date(string='Activity Deadline', default=fields.Date.today)
    
    # Attachments fields
    attachment_ids = fields.Many2many(comodel_name='ir.attachment', string='Bill Attachments')
    
    # Next action
    next_action_date = fields.Date(string='Next Action Date')

    def _compute_render_model(self):
        # OVERRIDES mail.renderer.mixin
        self.render_model = 'res.partner'

    @api.depends('template_id')
    def _compute_subject(self):
        for wizard in self:
            options = {
                'partner_id': wizard.partner_id.id if wizard.partner_id else False,
                'mail_template': wizard.template_id,
            }
            wizard.subject = self.env['supplier.followup.report']._get_email_subject(options)

    @api.depends('template_id')
    def _compute_body(self):
        # OVERRIDES mail.composer.mixin
        for wizard in self:
            options = {
                'partner_id': wizard.partner_id.id if wizard.partner_id else False,
                'mail_template': wizard.template_id,
            }
            wizard.body = self.env['supplier.followup.report']._get_main_body(options)

    def _get_default_body(self):
        """Generate default body for supplier payment reminder"""
        self.ensure_one()
        partner = self.partner_id
        
        # Format amounts properly
        total_due = formatLang(self.env, partner.total_due_supplier, currency_obj=partner.currency_id)
        total_overdue = formatLang(self.env, partner.total_overdue_supplier, currency_obj=partner.currency_id)
        
        body = _("""
        <p>Dear Accounts Payable Team,</p>
        <p>This is a reminder about pending payments to <b>%(supplier)s</b>.</p>
        <p>
            Total Due: <b>%(total_due)s</b><br/>
            Total Overdue: <b>%(total_overdue)s</b>
        </p>
        <p>Please review and process the payments as appropriate.</p>
        <p>Best regards,<br/>%(company)s</p>
        """) % {
            'supplier': partner.name,
            'total_due': total_due,
            'total_overdue': total_overdue,
            'company': self.env.company.name,
        }
        return body

    @api.depends('template_id')
    def _compute_email_recipient_ids(self):
        for wizard in self:
            partner = wizard.partner_id
            
            # Default to supplier follow-up responsible or current user
            responsible = partner.supplier_followup_responsible_id or self.env.user
            wizard.email_recipient_ids = responsible.partner_id
            
            if wizard.template_id:
                rendered_values = wizard.template_id._generate_template_recipients(
                    [partner.id],
                    {'partner_to', 'email_cc', 'email_to'},
                    True
                )[partner.id]
                if rendered_values.get('partner_ids'):
                    wizard.email_recipient_ids = [Command.link(partner_id) for partner_id in rendered_values['partner_ids']]

    @api.depends('sms_template_id')
    def _compute_sms_body(self):
        for wizard in self:
            options = {
                'partner_id': wizard.partner_id.id if wizard.partner_id else False,
                'sms_template': wizard.sms_template_id,
            }
            wizard.sms_body = self.env['supplier.followup.report']._get_sms_body(options)

    def _get_wizard_options(self):
        """Returns a dictionary of options from this wizard"""
        return {
            'partner_id': self.partner_id.id,
            'email': self.email,
            'email_from': self.template_id.email_from if self.template_id else self.env.company.email,
            'email_subject': self.subject,
            'email_recipient_ids': self.email_recipient_ids.ids if self.email_recipient_ids else [],
            'body': self.body,
            'attachment_ids': self.attachment_ids.ids,
            'sms': self.sms,
            'sms_body': self.sms_body,
            'print': self.print,
            'create_activity': self.create_activity,
            'activity_type_id': self.activity_type_id.id,
            'activity_summary': self.activity_summary,
            'activity_date_deadline': self.activity_date_deadline,
            'manual_followup': True,
        }

    def process_followup(self):
        """Process the supplier payment follow-up"""
        self.ensure_one()
        
        options = self._get_wizard_options()
        options['author_id'] = self.env.user.partner_id.id
        
        # Call execute_supplier_followup on the partner
        action = self.partner_id.execute_supplier_followup(options)
        
        return action or {'type': 'ir.actions.act_window_close'}