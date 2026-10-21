# -*- coding: utf-8 -*-

from odoo import fields, models

class User(models.Model):
    _inherit = 'res.users'

    inquiry_data = fields.Text('Inquiry Data', store=True, default='{}')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    active_product_inquiry = fields.Boolean(string='Inquiry Submit Action',related='website_id.active_product_inquiry',readonly=False)
    inquiry_submit_action = fields.Selection(string='Product Queries Action', related='website_id.inquiry_submit_action', readonly=False)
    inquiry_recipient_id = fields.Many2one('res.users', string='Recipient', related='website_id.inquiry_recipient_id',domain="[('share', '=', False)]",readonly=False)
    sales_person_id = fields.Many2one('res.users', string='Inquiry Salesperson', related='website_id.sales_person_id', readonly=False, domain="[('share', '=', False)]")
    sales_team_id = fields.Many2one('crm.team', string='Inquiry Sales Team', related='website_id.sales_team_id', readonly=False)
    inquiry_header = fields.Text(string='Header',  related='website_id.inquiry_header', readonly=False, translate=True)
    inquiry_desc_info = fields.Text(string='Information', related='website_id.inquiry_desc_info', readonly=False, translate=True)
    acknowledgement_message = fields.Text(string='Acknowledgement Message', related='website_id.acknowledgement_message', readonly=False, translate=True)

class CustomWebsite(models.Model):
    _inherit = 'website'

    def _default_sales_team_id(self):
        team = self.env.ref('sales_team.salesteam_website_sales', False)
        if team and team.active:
            return team.id
        else:
            return None

    inquiry_submit_action = fields.Selection(
        selection=[('email', 'Send An Email'),('crm', 'Create An Opportunity')],string='Inquiry Product Queries Action')
    sales_person_id = fields.Many2one('res.users', string='Inquiry Salesperson')
    sales_team_id = fields.Many2one('crm.team',string='Inquiry Sales Team', ondelete='set null',default=_default_sales_team_id)
    inquiry_recipient_id = fields.Many2one('res.users',string='Inquiry Recipient')
    inquiry_header = fields.Text('Inquiry Header', default='Have Questions ?', translate=True)
    inquiry_desc_info = fields.Text('Inquiry Information', default='We will follow up with you via email within 24-56 hours', translate=True)
    acknowledgement_message = fields.Text('Inquiry Acknowledgement Message', default='Thank You', translate=True)
