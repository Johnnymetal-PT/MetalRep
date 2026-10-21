# -*- coding: utf-8 -*-
import base64

from odoo import _, fields, models
from odoo.exceptions import UserError


class PartnerStatementActionWizard(models.TransientModel):
    _name = 'mh.partner.statement.action.wizard'
    _description = 'Acção para extracto / mapa de cobranças do parceiro'

    partner_id = fields.Many2one(
        'res.partner',
        string='Parceiro',
        required=True,
    )

    def action_view_map(self):
        """Abre o Mapa de Cobranças (interactivo) filtrado pelo parceiro."""
        self.ensure_one()
        return self.partner_id.open_collection_map()

    def action_send_email(self):
        """Gera PDF do Mapa de Cobranças e abre o composer de email."""
        self.ensure_one()
        partner = self.partner_id

        # 1. Gerar PDF do account.report Mapa de Cobranças
        report = self.env.ref('mh_accounting_reports.aged_customer_invoices_report')
        options = report.get_options(previous_options={
            'partner_ids': (partner | partner.commercial_partner_id).ids,
            'unfold_all': True,
        })
        try:
            pdf_content = report.export_to_pdf(options)['file_content']
        except Exception as e:
            raise UserError(_('Não foi possível gerar o PDF: %s') % str(e))

        filename = f'Mapa_Cobrancas_{partner.name}.pdf'.replace(' ', '_')

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
            'mh_accounting_reports.email_template_partner_statement',
            raise_if_not_found=False,
        )
        subject = _('%s — Mapa de Cobranças') % (partner.company_id.name or self.env.company.name)
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
            'name': _('Enviar Mapa de Cobranças por E-mail'),
            'res_model': 'mh.map.mail.composer',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
            'context': {
                'default_map_kind': 'statement',
                'default_partner_id': partner.id,
                'default_recipient_ids': [(6, 0, [partner.id])],
                'default_subject': subject,
                'default_body': body,
                'default_attachment_ids': [(6, 0, [attachment.id])],
            },
        }
