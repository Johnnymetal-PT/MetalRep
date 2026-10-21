# -*- coding: utf-8 -*-

import logging
from markupsafe import Markup
from odoo import models, fields, api, _
from odoo.tools import email_normalize
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class B2BApplication(models.Model):
    _name = "b2b.application"
    _description = "B2B Application"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(
        string="Application Number",
        required=True,
        copy=False,
        readonly=True,
        default="New",
    )
    street = fields.Char( required=True)
    street2 = fields.Char()
    city = fields.Char(string="City", required=True)
    state_id = fields.Many2one('res.country.state')
    zip = fields.Char(required=True)
    country_id = fields.Many2one('res.country', required=True)

    business_type_ids = fields.Many2many(
        'b2b.business.type',
        string="Type of Business",
        required=True
    )
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    first_name = fields.Char(string="First Name", required=True, tracking=True)
    last_name = fields.Char(string="Last Name", required=True, tracking=True)
    phone = fields.Char(string="Phone", required=True)
    email = fields.Char(string="Email", required=True)
    business_name = fields.Char(
        string="Business Name", required=True, tracking=True
    )
    business_number = fields.Char(string="Business Number", tracking=True)
    notes = fields.Text(string="Additional Notes")
    document_attachment = fields.Binary(string="Business Document", attachment=True)
    document_filename = fields.Char(string="Document Filename")
    terms_accepted = fields.Boolean(string="Terms Accepted", default=False)
    state = fields.Selection(
        [("draft", "Draft"), ("approved", "Approved"), ("rejected", "Rejected")],
        string="Status",
        default="draft",
        tracking=True,
    )
    partner_id = fields.Many2one("res.partner", string="Related Partner", tracking=True)
    rejection_reason = fields.Text(
        string='Rejection Reason',
        help='Reason for rejecting the application'
    )
    terms_and_conditions = fields.Html(
        string="Terms & Conditions",
        compute="_compute_terms_and_conditions",
        store=False
    )
    property_product_pricelist = fields.Many2one(
        comodel_name='product.pricelist',
        string="Pricelist",
        related='partner_id.property_product_pricelist', readonly=True,
        help="Pricelist used by this B2B partner"
    )

    #=== CONSTRAINS ===#
    _business_name_email_unique = models.Constraint(
        'unique(business_name, email)',
        'A record with the same Business Name or Email already exists.',
    )

    #=== CREATE METHOD ===#
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('b2b.application') or 'New'
        records = super().create(vals_list)
        for record in records:
            if record.state == 'draft':
                record._notify_admins_new_application()
        return records

    #=== COMPUTE METHODS ===#
    @api.depends()
    def _compute_terms_and_conditions(self):
        param = self.env['ir.config_parameter'].sudo().get_param(
            'b2b_application.terms_and_conditions'
        )
        for rec in self:
            rec.terms_and_conditions = param or ""

    #=== ACTION METHODS ===#
    def action_approve(self):
        self.ensure_one()
        return {
            'name': _('Approve B2B Application'),
            'type': 'ir.actions.act_window',
            'res_model': 'b2b.application.approval.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_application_id': self.id,
                'default_partner_id': self.partner_id.id if self.partner_id else False,
            }
        }

    def action_reject(self):
        """Open wizard to enter rejection reason"""
        self.ensure_one()
        return {
            'name': 'Reject Application',
            'type': 'ir.actions.act_window',
            'res_model': 'b2b.application.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_application_id': self.id,
            }
        }

    #=== OHER METHODS ===#
    def _get_admin_users(self):
        param_value = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("b2b_application.admin_user_ids", default="")
        )
        if not param_value:
            return self.env["res.users"]
        try:
            user_ids = [int(uid) for uid in param_value.split(",") if uid.isdigit()]
            return self.env["res.users"].browse(user_ids)
        except Exception:
            return self.env["res.users"]

    def _notify_admins_new_application(self):
        admin_users = self._get_admin_users()
        if not admin_users:
            return
        template = self.env.ref(
            "atharva_theme_base.email_template_b2b_application_admin_notification",
            raise_if_not_found=False,
        )
        if template:
            for admin in admin_users:
                template.with_context(admin_user=admin.name).send_mail(
                    self.id, force_send=True, email_values={"email_to": admin.email}
                )

    def _create_portal_user(self):
        """Create portal user for approved application"""
        existing_user = (
            self.env["res.users"].sudo().search([("login", "=", self.email),("name", "=", self.business_name)], limit=1)
        )
        if existing_user:
            raise ValidationError(
            _(
                "A portal user with the same email (%s) and name (%s) already exists. "
                "Please verify the information before proceeding."
            )
            % (self.email, self.first_name)
        )
        group_portal = self.env.ref('base.group_portal')
        try:
            b2b_user_id = self.env['res.users'].with_context(no_reset_password=True).sudo()._create_user_from_template({
                'name': self.business_name,
                'email': email_normalize(self.email),
                'login': email_normalize(self.email),
                'company_id': self.env.company.id,
                'company_ids': [(6, 0, self.env.company.ids)],
                'property_product_pricelist': self.property_product_pricelist.id if self.property_product_pricelist else False,
                'is_company': True,
                'group_ids': [(4, group_portal.id)],
                "active": True,
            })
            user_sudo = b2b_user_id.sudo()
            user_sudo.partner_id.signup_prepare()
            user_sudo.partner_id.update({
                'b2b_form_id': self.id,
                'company_type': 'company',
                'street': self.street,
                'street2': self.street2,
                'city': self.city,
                'state_id': self.state_id.id if self.state_id else False,
                'zip': self.zip,
                'country_id': self.country_id.id if self.country_id else False,
                'phone': self.phone,
                'property_product_pricelist': self.property_product_pricelist.id if self.property_product_pricelist else False,
            })

            user_sudo._action_reset_password(signup_type="reset")
            self.write({'state': 'approved', 'partner_id': user_sudo.partner_id.id})
            self._notify_applicant_status_change()

            return user_sudo

        except Exception as e:
            _logger.warning(f"Failed to create b2b user for {self.email}: {str(e)}")
            return False

    def _notify_applicant_status_change(self):
        if self.state == 'approved':
            approved_template_id = self.env.ref('atharva_theme_base.email_template_b2b_application_approved', raise_if_not_found=False)
            approved_template_id.send_mail(self.id, force_send=True)
            self.message_post(
                body=Markup(_(
                    "<p><b>B2B account has been successfully activated.</b></p>"
                    "<p>An email notification has been sent to: <b>%s</b></p>"
                    "<p><b>Assigned Pricelist:</b> %s</p>"
                ) % (self.partner_id.name, self.property_product_pricelist.name or "Not Set"),
            ))
        elif self.state == 'rejected':
            rejected_template_id = self.env.ref('atharva_theme_base.email_template_b2b_application_rejected', raise_if_not_found=False)
            rejected_template_id.send_mail(self.id, force_send=True)
            self.message_post(
                body=_(
                    "B2B application has been rejected.\n"
                    "An email has been sent to the requested user.\n"
                    "Rejection Reason: %s"
                ) % (self.rejection_reason or "Not specified")
            )

class MailMail(models.Model):
    _inherit = 'mail.mail'

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to replace Public User with OdooBot for B2B applications"""
        public_user = self.env.ref('base.public_user', raise_if_not_found=False)
        odoobot = self.env.ref('base.partner_root', raise_if_not_found=False)

        if not public_user or not odoobot:
            return super(MailMail, self).create(vals_list)

        public_partner_id = public_user.partner_id.id

        for vals in vals_list:
            if vals.get('model') == 'b2b.application':
                current_author_id = vals.get('author_id')
                if current_author_id:
                    if current_author_id == public_partner_id:
                        vals['author_id'] = odoobot.id
                else:
                    if self.env.user.id == public_user.id:
                        vals['author_id'] = odoobot.id
                    else:
                        vals['author_id'] = self.env.user.partner_id.id
        return super(MailMail, self).create(vals_list)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    b2b_form_id = fields.Many2one('b2b.application', 'B2B Form', readonly=True, copy=False)