# -*- coding: utf-8 -*-
import base64

from odoo import _, fields, models
from odoo.exceptions import UserError


class PartnerPaymentActionWizard(models.TransientModel):
    _name = 'mh.partner.payment.action.wizard'
    _description = 'Acção para mapa de pagamentos do fornecedor'

    partner_id = fields.Many2one(
        'res.partner',
        string='Parceiro',
        required=True,
    )

    def action_view_map(self):
        """Abre o Mapa de Pagamentos (interactivo) filtrado pelo fornecedor."""
        self.ensure_one()
        return self.partner_id.open_payment_map()

    def action_send_email(self):
        """Gera PDF do Mapa de Pagamentos e abre o composer de email."""
        self.ensure_one()
        partner = self.partner_id

        # 1. Gerar PDF do account.report Mapa de Pagamentos
        report = self.env.ref('mh_accounting_reports.aged_supplier_invoices_report')
        options = report.get_options(previous_options={
            'partner_ids': (partner | partner.commercial_partner_id).ids,
            'unfold_all': True,
        })
        try:
            pdf_content = report.export_to_pdf(options)['file_content']
        except Exception as e:
            raise UserError(_('Não foi possível gerar o PDF: %s') % str(e))

        filename = f'Mapa_Pagamentos_{partner.name}.pdf'.replace(' ', '_')

        # 2. Criar attachment temporário (sem res_model/res_id para não
        #    aparecer autonomamente na caixa de anexos do contacto)
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'datas': base64.b64encode(pdf_content),
            'type': 'binary',
            'mimetype': 'application/pdf',
        })

        # 3. Renderizar assunto/corpo a partir do template
        template = self.env.ref(
            'mh_accounting_reports.email_template_partner_payment',
            raise_if_not_found=False,
        )
        subject = _('%s — Mapa de Pagamentos') % (partner.company_id.name or self.env.company.name)
        body = ''
        if template:
            rendered = template._generate_template(
                [partner.id], ('subject', 'body_html'),
            )
            vals = rendered.get(partner.id, {})
            subject = vals.get('subject') or subject
            body = vals.get('body_html') or ''

        # 4. Abrir o NOSSO composer (controlo total dos destinatários)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Enviar Mapa de Pagamentos por E-mail'),
            'res_model': 'mh.map.mail.composer',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
            'context': {
                'default_map_kind': 'payment',
                'default_partner_id': partner.id,
                'default_recipient_ids': [(6, 0, [partner.id])],
                'default_subject': subject,
                'default_body': body,
                'default_attachment_ids': [(6, 0, [attachment.id])],
            },
        }
