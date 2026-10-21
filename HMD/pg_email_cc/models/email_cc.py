# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.
import logging
import threading

from odoo import SUPERUSER_ID, api, fields, models, registry
from odoo.tools.misc import clean_context, split_every

_logger = logging.getLogger(__name__)

class AccountMoveeSend(models.AbstractModel):
    _inherit = "account.move.send"
    _abstract = True

    email_to = fields.Char(string="Email CC")

    def _get_wizard_values(self):
        self.ensure_one()
        return {
            'mail_template_id': self.mail_template_id.id,
            'sp_partner_id': self.env.user.partner_id.id,
            'sp_user_id': self.env.user.id,
            'download': self.checkbox_download,
            'send_mail': self.checkbox_send_mail,
            'email_cc': self.email_to,
        }

    def _get_mail_move_values(self, move, wizard=None):
        mail_template_id = move.send_and_print_values and move.send_and_print_values.get('mail_template_id')
        mail_template = wizard and wizard.mail_template_id or self.env['mail.template'].browse(mail_template_id)
        mail_lang = self._get_default_mail_lang(move, mail_template)
        return {
            'mail_template_id': mail_template,
            'mail_lang': mail_lang,
            'mail_body': wizard and wizard.mail_body or self._get_default_mail_body(move, mail_template, mail_lang),
            'mail_subject': wizard and wizard.mail_subject or self._get_default_mail_subject(move, mail_template, mail_lang),
            'mail_partner_ids': wizard and wizard.mail_partner_ids or self._get_default_mail_partner_ids(move, mail_template, mail_lang),
            'mail_attachments_widget': wizard and wizard.mail_attachments_widget or self._get_default_mail_attachments_widget(move, mail_template),
            'email_cc':self.email_to,
        }

    @api.model
    def _send_mails(self, moves_data):
        subtype = self.env.ref('mail.mt_comment')

        for move, move_data in [(move, move_data) for move, move_data in moves_data.items() if move.partner_id.email]:
            mail_template = move_data['mail_template_id']
            mail_lang = move_data['mail_lang']
            mail_params = self._get_mail_params(move, move_data)
            if not mail_params:
                continue

            if move_data.get('proforma_pdf_attachment'):
                attachment = move_data['proforma_pdf_attachment']
                mail_params['attachments'].append((attachment.name, attachment.raw))

            email_from = self._get_mail_default_field_value_from_template(mail_template, mail_lang, move, 'email_from')
            model_description = move.with_context(lang=mail_lang).type_name

            self._send_mail(
                move,
                mail_template,
                subtype_id=subtype.id,
                model_description=model_description,
                email_from=email_from,
                email_cc=move_data.get('email_cc'),
                **mail_params,
            )

class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    email_to = fields.Char(string="Email CC")
    additional_email = fields.Char(string="Additional email")  # Optional

    def _prepare_mail_values(self, res_ids):
        mail_values_all = super(MailComposeMessage, self)._prepare_mail_values(res_ids)

        for res_id, mail_values in mail_values_all.items():
            # Always set email_from to current user
            sender_email = self.env.user.email_formatted or 'catchall@yourdomain.com'
            mail_values["email_from"] = sender_email
            mail_values["reply_to"] = sender_email  # Always match From

            # Optional: set CC if filled in
            if self.email_to:
                mail_values["email_cc"] = self.email_to

            # Optional: include additional email as fallback or custom usage
            # if self.additional_email:
            #     mail_values["email_cc"] = (mail_values.get("email_cc") or "") + "," + self.additional_email

        return mail_values_all

class MailThreadInherit(models.AbstractModel):
    _inherit = "mail.thread"


    def _get_notify_valid_parameters(self):
        """ Several parameters exist for notification methods as business
        flows often want to customize the standard notification experience.
        In order to ease coding kwargs are frequently used. This method
        acts like a filter, allowing to spot parameters that are not
        supported. """
        return {
            'force_email_company',
            'force_email_lang',
            'force_send',
            'email_cc',
            'mail_auto_delete',
            'model_description',
            'notify_author',
            'resend_existing',
            'scheduled_date',
            'send_after_commit',
            'skip_existing',
            'subtitles',
        }

    def _notify_thread_by_email(self, message, recipients_data, msg_vals=False,
                                mail_auto_delete=True,  # mail.mail
                                model_description=False, force_email_company=False, force_email_lang=False,  # rendering
                                subtitles=None,  # rendering
                                resend_existing=False, force_send=True, send_after_commit=True,  # email send
                                **kwargs):
        """ Method to send emails notifications linked to a message.

        :param record message: <mail.message> record being notified. May be
          void as 'msg_vals' superseeds it;
        :param list recipients_data: list of recipients data based on <res.partner>
          records formatted like [
          {
            'active': partner.active;
            'id': id of the res.partner being recipient to notify;
            'is_follower': follows the message related document;
            'lang': its lang;
            'groups': res.group IDs if linked to a user;
            'notif': 'inbox', 'email', 'sms' (SMS App);
            'share': is partner a customer (partner.partner_share);
            'type': partner usage ('customer', 'portal', 'user');
            'ushare': are users shared (if users, all users are shared);
          }, {...}]. See ``MailThread._notify_get_recipients()``;
        :param dict msg_vals: values dict used to create the message, allows to
          skip message usage and spare some queries;

        :param bool mail_auto_delete: delete notification emails once sent;

        :param str model_description: description of current model, given to
          avoid fetching it and easing translation support;
        :param record force_email_company: <res.company> record used when rendering
          notification layout. Otherwise computed based on current record;
        :param str force_email_lang: lang used when rendering content, used
          notably to compute model name or translate access buttons;
        :param list subtitles: optional list set as template value "subtitles";

        :param bool resend_existing: check for existing notifications to update
          based on mailed recipient, otherwise create new notifications;
        :param bool force_send: send emails directly instead of using queue;
        :param bool send_after_commit: if force_send, tells to send emails after
          the transaction has been committed using a post-commit hook;
        """
        partners_data = [r for r in recipients_data if r['notif'] == 'email']
        if not partners_data:
            return True

        base_mail_values = self._notify_by_email_get_base_mail_values(
            message,
            additional_values={'auto_delete': mail_auto_delete}
        )

        email_cc = kwargs.get("email_cc")
        email_to = kwargs.get("email_to")
        if email_cc:
            msg_vals.update({"email_cc": email_cc})
        if email_to:
            msg_vals.update({"email_to": email_to})

        # Clean the context to get rid of residual default_* keys that could cause issues during
        # the mail.mail creation.
        # Example: 'default_state' would refer to the default state of a previously created record
        # from another model that in turns triggers an assignation notification that ends up here.
        # This will lead to a traceback when trying to create a mail.mail with this state value that
        # doesn't exist.
        SafeMail = self.env['mail.mail'].sudo().with_context(clean_context(self._context))
        SafeNotification = self.env['mail.notification'].sudo().with_context(clean_context(self._context))
        emails = self.env['mail.mail'].sudo()

        # loop on groups (customer, portal, user,  ... + model specific like group_sale_salesman)
        notif_create_values = []
        recipients_max = 50
        add_additional_email = False
        add_additional_cc = False

        for _lang, render_values, recipients_group in self._notify_get_classified_recipients_iterator(
                message,
                partners_data,
                msg_vals=msg_vals,
                model_description=model_description,
                force_email_company=force_email_company,
                force_email_lang=force_email_lang,
                subtitles=subtitles,
        ):
            # generate notification email content
            mail_body = self._notify_by_email_render_layout(
                message,
                recipients_group,
                msg_vals=msg_vals,
                render_values=render_values,
            )
            recipients_ids = recipients_group.pop('recipients')

            # create email
            for recipients_ids_chunk in split_every(recipients_max, recipients_ids):
                mail_values = self._notify_by_email_get_final_mail_values(
                    recipients_ids_chunk,
                    base_mail_values,
                    additional_values={'body_html': mail_body}
                )
                if msg_vals and msg_vals.get("email_to") and not add_additional_email:
                    add_additional_email = True
                    mail_values.update(
                        {"additional_email_to": msg_vals.get("email_to")}
                    )
                if msg_vals and msg_vals.get("email_cc") and not add_additional_cc:
                    add_additional_cc = True
                    mail_values.update({"email_cc": msg_vals.get("email_cc")})
                new_email = SafeMail.create(mail_values)

                if new_email and recipients_ids_chunk:
                    tocreate_recipient_ids = list(recipients_ids_chunk)
                    if resend_existing:
                        existing_notifications = self.env['mail.notification'].sudo().search([
                            ('mail_message_id', '=', message.id),
                            ('notification_type', '=', 'email'),
                            ('res_partner_id', 'in', tocreate_recipient_ids)
                        ])
                        if existing_notifications:
                            tocreate_recipient_ids = [rid for rid in recipients_ids_chunk if
                                                      rid not in existing_notifications.mapped('res_partner_id.id')]
                            existing_notifications.write({
                                'notification_status': 'ready',
                                'mail_mail_id': new_email.id,
                            })
                    notif_create_values += [{
                        'author_id': message.author_id.id,
                        'is_read': True,  # discard Inbox notification
                        'mail_mail_id': new_email.id,
                        'mail_message_id': message.id,
                        'notification_status': 'ready',
                        'notification_type': 'email',
                        'res_partner_id': recipient_id,
                    } for recipient_id in tocreate_recipient_ids]
                emails += new_email

        if notif_create_values:
            SafeNotification.create(notif_create_values)

        # NOTE:
        #   1. for more than 50 followers, use the queue system
        #   2. do not send emails immediately if the registry is not loaded,
        #      to prevent sending email during a simple update of the database
        #      using the command-line.
        test_mode = getattr(threading.current_thread(), 'testing', False)
        force_send = self.env.context.get('mail_notify_force_send', force_send)
        if force_send and len(emails) < recipients_max and (not self.pool._init or test_mode):
            # unless asked specifically, send emails after the transaction to
            # avoid side effects due to emails being sent while the transaction fails
            if not test_mode and send_after_commit:
                email_ids = emails.ids
                dbname = self.env.cr.dbname
                _context = self._context

                @self.env.cr.postcommit.add
                def send_notifications():
                    db_registry = registry(dbname)
                    with db_registry.cursor() as cr:
                        env = api.Environment(cr, SUPERUSER_ID, _context)
                        env['mail.mail'].browse(email_ids).send()
            else:
                emails.send()

        return True

