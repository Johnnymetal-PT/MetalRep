# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import plaintext2html, html2plaintext
from odoo.tools.misc import formatLang, format_date, get_lang

_logger = logging.getLogger(__name__)


class SupplierFollowupReport(models.AbstractModel):
    _name = 'supplier.followup.report'
    _description = 'Supplier Follow-up Report'
    
    def get_followup_report_html(self, options):
        """
        Return the html of the followup report, based on the report options.
        This uses the template body from _get_main_body which uses our email templates.
        """
        return self._get_main_body(options)
    
    @api.model
    def _get_rendered_body(self, partner_id, template_src, default_body, **kwargs):
        """ Returns the body that can be rendered by the template_src, or if None, returns the default_body.
        kwargs can contain any keyword argument supported by the _render_template function
        """
        if template_src:
            return self.env['mail.composer.mixin'].sudo()._render_template(
                template_src, 
                'res.partner', 
                [partner_id], 
                **kwargs
            )[partner_id]
        return default_body

    @api.model
    def _get_main_body(self, options):
        # Manual follow-up: return body from options
        if options.get('body'):
            return options.get('body')

        partner = self.env['res.partner'].browse(options.get('partner_id'))
        followup_line = options.get('followup_line', partner.supplier_followup_line_id)
        
        # Try to get supplier template first, then fallback to normal template
        mail_template = options.get('mail_template')
        if not mail_template and followup_line:
            mail_template = followup_line.supplier_mail_template_id or followup_line.mail_template_id
        
        # If still no template, try to get default internal template
        if not mail_template:
            try:
                mail_template = self.env.ref('supplier_followup.email_template_supplier_payment_reminder_internal')
            except:
                pass
        
        template_src = None
        if mail_template:
            template_src = mail_template.with_context(lang=partner.lang or self.env.user.lang).body_html

        partner_followup_responsible_id = partner.supplier_followup_responsible_id or self.env.user
        responsible_signature = partner_followup_responsible_id.signature or partner_followup_responsible_id.name
        self = self.with_context(lang=partner.lang or self.env.user.lang)
        
        # Format amounts properly for default body
        total_due = formatLang(self.env, partner.total_due_supplier, currency_obj=partner.currency_id)
        total_overdue = formatLang(self.env, partner.total_overdue_supplier, currency_obj=partner.currency_id)
        
        default_body = _("""Dear Accounts Payable Team,

This is an urgent reminder about pending payments to %s.

Our records show:
- Total Amount We Owe: %s
- Overdue Amount: %s

Please review and process these payments immediately to maintain our good standing with this supplier.

Best Regards,

""") % (partner.name, total_due, total_overdue)

        default_body_html = plaintext2html(default_body) + responsible_signature  # responsible_signature is an html field
        return self._get_rendered_body(
            partner.id, 
            template_src, 
            default_body_html, 
            engine='qweb', 
            options={'post_process': True}
        )

    @api.model
    def _get_email_subject(self, options):
        # Manual follow-up: return body from options
        if options.get('email_subject'):
            return options.get('email_subject')

        partner = self.env['res.partner'].browse(options.get('partner_id'))
        followup_line = options.get('followup_line', partner.supplier_followup_line_id)
        
        # Try to get supplier template first
        mail_template = options.get('mail_template')
        if not mail_template and followup_line:
            mail_template = followup_line.supplier_mail_template_id or followup_line.mail_template_id
        
        # If still no template, try to get default internal template
        if not mail_template:
            try:
                mail_template = self.env.ref('supplier_followup.email_template_supplier_payment_reminder_internal')
            except:
                pass
                
        template_src = None
        if mail_template:
            template_src = mail_template.with_context(lang=partner.lang or self.env.user.lang).subject

        partner_name = partner.name
        company_name = self.env.company.name
        self = self.with_context(lang=partner.lang or self.env.user.lang)
        default_subject = _("%(company)s Pagamento Necessário - %(partner)s", company=company_name, partner=partner_name)

        return self._get_rendered_body(
            partner.id, 
            template_src, 
            default_subject, 
            options={'post_process': True}
        )

    @api.model
    def _get_sms_body(self, options):
        # Manual follow-up: return body from options
        if options.get('sms_body'):
            return options.get('sms_body')

        partner = self.env['res.partner'].browse(options.get('partner_id'))
        followup_line = options.get('followup_line', partner.supplier_followup_line_id)
        
        sms_template = options.get('sms_template')
        if not sms_template and followup_line:
            sms_template = followup_line.supplier_sms_template_id or followup_line.sms_template_id
            
        template_src = None
        if sms_template:
            template_src = sms_template.with_context(lang=partner.lang or self.env.user.lang).body

        partner_followup_responsible_id = partner.supplier_followup_responsible_id or self.env.user
        responsible_signature = html2plaintext(partner_followup_responsible_id.signature or partner_followup_responsible_id.name)
        self = self.with_context(lang=partner.lang or self.env.user.lang)
        
        # Format amount for SMS
        total_overdue = formatLang(self.env, partner.total_overdue_supplier, currency_obj=partner.currency_id)
        
        default_body = _("Urgente: Pagamento a %s em atraso. Valor: %s. Por favor processe de imediato. %s") % (
                        partner.name, total_overdue, responsible_signature)

        return self._get_rendered_body(
            partner.id, 
            template_src, 
            default_body, 
            options={'post_process': True}
        )
    
    @api.model
    def _get_email_from(self, options):
        partner = self.env['res.partner'].browse(options.get('partner_id'))
        # For manual followups, get the email_from from the selected template in the send & print wizard.
        if options.get('email_from'):
            followup_email_from = options['email_from']
        # For automatic followups, get it from mail template on the followup line.
        else:
            followup_line = options.get('followup_line') or partner.supplier_followup_line_id
            mail_template = options.get('mail_template')
            if not mail_template and followup_line:
                mail_template = followup_line.supplier_mail_template_id or followup_line.mail_template_id
            followup_email_from = mail_template.email_from if mail_template else False
        # The _render_template() function formats the email content. It handles cases where the email_from value
        # is a template that needs evaluation. For instance, "{{ object.supplier_followup_responsible_id.email_formatted }}".
        if followup_email_from:
            return self.env['mail.composer.mixin'].sudo()._render_template(followup_email_from, 'res.partner', [partner.id])[partner.id] or None
        return self.env.user.email_formatted or self.env.company.email_formatted
    
    @api.model
    def _get_email_reply_to(self, options):
        partner = self.env['res.partner'].browse(options.get('partner_id'))
        followup_line = options.get('followup_line', partner.supplier_followup_line_id)
        mail_template = options.get('mail_template')
        if not mail_template and followup_line:
            mail_template = followup_line.supplier_mail_template_id or followup_line.mail_template_id
        # if template has no reply-to set, fall back to default reply-to, otherwise
        # it will be set to False and behave unexpectedly
        if mail_template and mail_template.reply_to:
            followup_reply_to = mail_template.reply_to
        else:
            followup_reply_to = self.env.company.email or self.env.user.email
        return followup_reply_to
    
    @api.model
    def _send_email(self, options):
        """
        Send by email the followup to the supplier's followup contacts
        """
        partner = self.env['res.partner'].browse(options.get('partner_id'))
        followup_line = options.get('followup_line', partner.supplier_followup_line_id)
        
        # For supplier followup, send to internal responsible, not to supplier
        recipient_ids = options.get('email_recipient_ids', [])
        if recipient_ids:
            # Convert IDs to recordset if necessary
            if isinstance(recipient_ids, list):
                followup_recipients = self.env['res.partner'].browse(recipient_ids)
            else:
                followup_recipients = recipient_ids
        else:
            responsible = partner.supplier_followup_responsible_id or self.env.user
            followup_recipients = responsible.partner_id
        
        # Generate PDF attachment for the supplier followup report
        supplier_report = self.env.ref('supplier_followup.supplier_followup_report')
        report_options = supplier_report.get_options(
            previous_options={
                'partner_ids': [partner.id],
                'unfold_all': True,
                'filter_unreconciled': True,
            }
        )
        
        # Filter journals - exclude only general type journals
        if 'journals' in report_options:
            for journal in report_options['journals']:
                # Select all journals except general type
                journal['selected'] = journal.get('type') != 'general'
        
        # Generate the PDF
        pdf_content = supplier_report.with_context(
            lang=partner.lang or self.env.user.lang
        ).export_to_pdf(report_options)
        
        # Create PDF attachment
        tz_date_str = format_date(self.env, fields.Date.today(), lang_code=self.env.user.lang or get_lang(self.env).code)
        tz_date_str = tz_date_str.replace('.', '-')
        
        pdf_attachment = self.env['ir.attachment'].create([{
            'name': f"{partner.name} - Supplier Follow-up {tz_date_str}.pdf",
            'res_model': 'res.partner',
            'res_id': partner.id,
            'type': 'binary',
            'raw': pdf_content['file_content'],
            'mimetype': 'application/pdf',
        }])
        
        # Get existing attachments and add our PDF
        attachment_ids = options.get('attachment_ids', [])
        if attachment_ids:
            attachment_ids = list(attachment_ids)
        attachment_ids.append(pdf_attachment.id)
        
        sent_at_least_once = False
        for to_send_partner in followup_recipients:
            email = to_send_partner.email
            if email and email.strip():
                self = self.with_context(lang=partner.lang or self.env.user.lang)
                body_html = self.with_context(mail=True).get_followup_report_html(options)

                # If the follow-up was executed manually, the author_id will be set to the ID of the current logged-in user.
                # Otherwise, if the follow-up is automatic, the author_id will be the followup responsible or OdooBot.
                author_id = options.get('author_id', self.env.user.partner_id.id)

                partner.with_context(mail_post_autofollow=True, mail_notify_author=True, lang=partner.lang or self.env.user.lang).message_post(
                    partner_ids=[to_send_partner.id],
                    author_id=author_id,
                    email_from=self._get_email_from(options),
                    body=body_html,
                    subject=self._get_email_subject(options),
                    reply_to=self._get_email_reply_to(options),
                    model_description=_('lembrete de pagamento a fornecedor'),
                    email_layout_xmlid='mail.mail_notification_light',
                    attachment_ids=attachment_ids,
                    subtype_id=self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note'),
                )
                sent_at_least_once = True

                # add additional followers to the partner's chatter
                if followup_line and hasattr(followup_line, 'additional_follower_ids') and followup_line.additional_follower_ids:
                    partner.message_subscribe(followup_line.additional_follower_ids.partner_id.ids)
        
        if not sent_at_least_once:
            raise UserError(_("You are trying to send an Email, but no follow-up contact has any email address set for supplier '%s'", partner.name))
    
    @api.model
    def _send_sms(self, options):
        """
        Send by SMS the followup to the supplier
        """
        partner = self.env['res.partner'].browse(options.get('partner_id'))
        # For supplier followup, send to internal responsible, not to supplier
        recipient_ids = options.get('sms_recipient_ids') or options.get('email_recipient_ids', [])
        if recipient_ids:
            # Convert IDs to recordset if necessary
            if isinstance(recipient_ids, list):
                followup_contacts = self.env['res.partner'].browse(recipient_ids)
            else:
                followup_contacts = recipient_ids
        else:
            responsible = partner.supplier_followup_responsible_id or self.env.user
            followup_contacts = responsible.partner_id
        
        sent_at_least_once = False
        for to_send_partner in followup_contacts:
            sms_number = to_send_partner.mobile or to_send_partner.phone
            if sms_number:
                sms_body = self.with_context(lang=partner.lang or self.env.user.lang)._get_sms_body(options)
                partner._message_sms(
                    body=sms_body,
                    partner_ids=partner.ids,
                    sms_pid_to_number={partner.id: sms_number},
                )
                sent_at_least_once = True
        if not sent_at_least_once:
            raise UserError(_("Está a tentar enviar um SMS, mas nenhum contacto de follow-up tem número de telemóvel/telefone definido para o fornecedor. '%s'", partner.name))
    
    @api.model
    def _print_supplier_followup_letter(self, partner, options=None):
        """Generate the supplier followup letter for the given partner.
        The letter is saved as ir.attachment and linked in the chatter.
        
        Returns a client action downloading this letter and closing the wizard.
        """
        # Get our supplier followup report
        supplier_report = self.env.ref('supplier_followup.supplier_followup_report')
        
        # Build options for the report with supplier-specific filters
        report_options = supplier_report.get_options(
            previous_options={
                'partner_ids': (partner | partner.commercial_partner_id).ids,
                'unfold_all': True,
                'filter_unreconciled': True,
            }
        )
        
        # Filter journals - exclude only general type journals
        if 'journals' in report_options:
            for journal in report_options['journals']:
                # Select all journals except general type
                journal['selected'] = journal.get('type') != 'general'
        
        # Merge with any additional options passed
        if options:
            report_options.update(options)
        
        # Generate the PDF directly using export_to_pdf from account.report
        pdf_content = supplier_report.with_context(
            lang=partner.lang or self.env.user.lang
        ).export_to_pdf(report_options)
        
        # Generate filename
        tz_date_str = format_date(self.env, fields.Date.today(), lang_code=self.env.user.lang or get_lang(self.env).code)
        tz_date_str = tz_date_str.replace('.', '-')
        
        # Create attachment using the pdf_content dict directly
        attachment = self.env['ir.attachment'].create([
            {
                'name': f"{partner.name} - Follow-up de Fornecedor {tz_date_str}.pdf",
                'res_model': 'res.partner',
                'res_id': partner.id,
                'type': 'binary',
                'raw': pdf_content['file_content'],
                'mimetype': 'application/pdf',
            },
        ])
        
        partner.message_post(body=_('Relatório de follow-up de fornecedor gerado'), attachment_ids=[attachment.id])
        
        return {
            'type': 'ir.actions.client',
            'tag': 'close_followup_wizard',
            'params': {
                'url': '/web/content/%s?download=1' % attachment.id,
            }
        }