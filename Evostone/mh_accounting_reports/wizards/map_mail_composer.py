# -*- coding: utf-8 -*-
from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MapMailComposer(models.TransientModel):
    _name = 'mh.map.mail.composer'
    _description = 'Composer de e-mail dos Mapas (Cobranças/Pagamentos)'

    map_kind = fields.Selection(
        [('statement', 'Mapa de Cobranças'),
         ('payment', 'Mapa de Pagamentos')],
        string='Tipo de Mapa',
        required=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Parceiro',
        required=True,
        readonly=True,
    )
    recipient_ids = fields.Many2many(
        'res.partner',
        'mh_map_mail_composer_partner_rel',
        'composer_id', 'partner_id',
        string='Para',
        help='Destinatários principais (por defeito, o próprio parceiro).',
    )
    cc_partner_ids = fields.Many2many(
        'res.partner',
        'mh_map_mail_composer_cc_rel',
        'composer_id', 'partner_id',
        string='Cc',
        default=lambda self: self._default_cc_partners(),
        help='Contactos em cópia. Por defeito, os utilizadores configurados '
             'nas Definições de Contabilidade. Podem ser retirados/adicionados.',
    )
    cc_preview = fields.Char(
        string='Emails em Cc',
        compute='_compute_cc_preview',
        help='Pré-visualização dos endereços que vão em cópia.',
    )

    @api.model
    def _default_cc_partners(self):
        """Cc por defeito = contactos dos utilizadores configurados em
        Definições de Contabilidade (company.mh_map_cc_user_ids)."""
        partners = self.env.company.mh_map_cc_user_ids.partner_id
        return [(6, 0, partners.ids)]

    @api.depends('cc_partner_ids', 'cc_partner_ids.email', 'cc_partner_ids.name')
    def _compute_cc_preview(self):
        for comp in self:
            comp.cc_preview = ', '.join(
                p.email if p.email else '%s (sem email)' % p.name
                for p in comp.cc_partner_ids
            )
    subject = fields.Char(string='Assunto', required=True)
    body = fields.Html(string='Mensagem', sanitize_style=True)
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'mh_map_mail_composer_attachment_rel',
        'composer_id', 'attachment_id',
        string='Anexos',
    )

    def action_send(self):
        """Envia o e-mail directamente (mail.mail) aos destinatários
        escolhidos + Cc, sem envolver os followers do contacto. Regista
        uma nota no chatter do parceiro para auditoria."""
        self.ensure_one()

        if not self.recipient_ids and not self.cc_partner_ids:
            raise UserError(_('Indique pelo menos um destinatário ou Cc.'))

        # Lista de e-mails "Para" a partir dos parceiros (ignora sem e-mail)
        to_emails = [p.email for p in self.recipient_ids if p.email]
        partners_sem_email = self.recipient_ids.filtered(lambda p: not p.email)
        if partners_sem_email:
            raise UserError(_(
                'Os seguintes destinatários não têm e-mail definido:\n%s'
            ) % '\n'.join('- %s' % p.display_name for p in partners_sem_email))

        # Cc a partir dos contactos escolhidos — erro se algum não tiver e-mail
        cc_sem_email = self.cc_partner_ids.filtered(lambda p: not p.email)
        if cc_sem_email:
            raise UserError(_(
                'Os seguintes contactos em Cc não têm e-mail definido:\n%s'
            ) % '\n'.join('- %s' % p.display_name for p in cc_sem_email))
        cc_emails = ', '.join(p.email_formatted for p in self.cc_partner_ids)

        email_from = (self.env.company.email_formatted
                      or self.env.user.email_formatted)

        # Enviar e-mail directo (sem model/res_id → não cria entrada própria
        # no chatter; o registo é feito por nós abaixo, numa única nota).
        mail = self.env['mail.mail'].sudo().create({
            'subject': self.subject,
            'body_html': self.body,
            'email_from': email_from,
            'email_to': ','.join(to_emails) if to_emails else False,
            'email_cc': cc_emails or False,
            'attachment_ids': [(6, 0, self.attachment_ids.ids)],
            'auto_delete': True,
        })
        mail.send()

        # Registo único no chatter (nota — sem destinatários, não notifica
        # ninguém): corpo do e-mail dentro de uma caixa azul, com o assunto
        # como título da mensagem.
        body = Markup(
            '<div style="background-color:#E2F3F6; border-radius:6px; '
            'padding:12px 16px; max-width:91%%; margin:0;">'
            '<p style="font-style:italic; color:#7f8c8d; font-size:13px; margin:0 0 8px 0;">'
            'Assunto: %(subject)s</p>'
            '%(content)s'
            '</div>'
        ) % {
            'subject': self.subject or '',
            'content': self.body or Markup(''),
        }
        self.partner_id.message_post(
            subject=self.subject,
            body=body,
            subtype_xmlid='mail.mt_note',
            attachment_ids=self.attachment_ids.ids,
        )

        return {'type': 'ir.actions.act_window_close'}
