# -*- coding: utf-8 -*-

import base64
import logging
import werkzeug.exceptions

from odoo import http, _
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome

_logger = logging.getLogger(__name__)

class B2BSignupController(AuthSignupHome):

    @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False, captcha='signup')
    def block_signup_if_b2b_enabled(self, *args, **kw):
        """ This method is used to block the signup if B2B is enabled. """
        website = request.website.sudo()
        has_query_params = bool(request.httprequest.args)
        if website.active_b2b_signup and website.active_b2b_mode and not has_query_params:
            raise werkzeug.exceptions.NotFound()

        return super().web_auth_signup(*args, **kw)

class B2BApplicationController(http.Controller):

    @http.route('/b2b_terms', type='http', auth='public', website=True)
    def terms_conditions(self, **kwargs):
        """ This method is used to display the B2B terms and conditions page. """
        website = request.env['website'].get_current_website()
        return request.render("atharva_theme_base.default_b2b_terms_conditions_page", {'website': website})

    @http.route('/b2b/get_states', type='jsonrpc', auth='public', methods=['POST'], csrf=False)
    def get_states(self, country_id, **kwargs):
        """Get states for a given country"""
        try:
            if not country_id:
                _logger.warning("No country_id provided")
                return []

            states = request.env['res.country.state'].sudo().search([
                ('country_id', '=', int(country_id))
            ], order='name')

            result = [{
                'id': state.id,
                'name': state.name,
                'code': state.code
            } for state in states]

            return result
        except Exception as e:
            _logger.exception("Error fetching states for country_id=%r: %s", country_id, e)
            return []

    @http.route('/web/b2b_signup', type='http', auth='public', website=True)
    def application_form(self, **kw):
        """ This method is used to display the B2B application form. """

        website = request.website.sudo()
        if not (website.active_b2b_signup and website.active_b2b_mode):
            raise werkzeug.exceptions.NotFound()

        countries = request.env['res.country'].sudo().search([], order='name')
        states = request.env['res.country.state'].sudo().search([], order='name')
        business_types = request.env['b2b.business.type'].sudo().search([], order='name')
        terms_and_conditions = website.b2b_terms_and_conditions;

        return request.render('theme_alan.application_form_template', {
            'countries': countries,
            'states': states,
            'business_types': business_types,
            'terms_and_conditions': terms_and_conditions,
        })

    @http.route('/web/b2b_signup/submit', type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def application_submit(self, **post):
        """ This method is used to submit the B2B application form. """
        try:
            _logger.info("Received POST data keys: %s", list(post.keys()))

            # --- Helper to extract safe value ---
            def get_value(key, default=''):
                val = post.get(key, default)
                if isinstance(val, list):
                    return val[0] if val else default
                return val if val else default

            email = get_value('email')

            # --- Check for existing application with same email ---
            existing_application = request.env['b2b.application'].sudo().search([
                ('email', '=', email)
            ], limit=1)

            if existing_application:
                return request.render('theme_alan.application_error_template', {
                    'error_message': 'An application with this email address already exists. If you need assistance, please contact support.',
                    'error_title': 'Duplicate Application'
                })

            # --- Check for existing user with same email ---
            existing_user = request.env['res.users'].sudo().search([
                ('login', '=', email)
            ], limit=1)

            if existing_user:
                return request.render('theme_alan.application_error_template', {
                    'error_message': 'An account with this email address already exists. Please use the login page to access your account.',
                    'error_title': 'Account Already Exists'
                })

            # --- Handle File Upload ---
            document_data = False
            document_filename = False
            files = request.httprequest.files
            if files and 'document_attachment' in files:
                file_data = files['document_attachment']
                if file_data and file_data.filename:
                    document_data = base64.b64encode(file_data.read())
                    document_filename = file_data.filename
                    _logger.info(" Uploaded document: %s", document_filename)

            # ---- Handle Multiple Business Types ----
            business_types = []
            if hasattr(request.httprequest.form, 'getlist'):
                business_types = request.httprequest.form.getlist('business_type')
            if not business_types and 'business_type' in post:
                val = post.get('business_type')
                if isinstance(val, (list, tuple)):
                    business_types = val
                elif val:
                    business_types = [val]
            _logger.info(" Selected Business Types: %s", business_types)

            business_type_ids = []
            if business_types:
                BusinessType = request.env['b2b.business.type'].sudo()
                for btype in business_types:
                    record = BusinessType.search([('name', '=ilike', btype.strip())], limit=1)
                    if record:
                        business_type_ids.append(record.id)
                    else:
                        _logger.warning(" Business Type not found: %s", btype)
            _logger.info(" Final Business Type IDs: %s", business_type_ids)

            vals = {
                'first_name': get_value('first_name'),
                'last_name': get_value('last_name'),
                'phone': get_value('phone'),
                'email': email,
                'business_name': get_value('business_name'),
                'business_number': get_value('business_number'),
                'business_type_ids': [(6, 0, business_type_ids)],
                'street': get_value('street'),
                'street2': get_value('street2'),
                'city': get_value('city'),
                'state_id': get_value('state_id'),
                'zip': get_value('zip'),
                'country_id': get_value('country_id'),
                'notes': get_value('notes'),
                'document_attachment': document_data,
                'document_filename': document_filename,
                'terms_accepted': bool(get_value('terms_accepted')),
                'state': 'draft',
            }

            application = request.env['b2b.application'].sudo().create(vals)
            _logger.info("B2B Application created id=%s email=%s", application.id, email)

            return request.render('theme_alan.application_thank_you_template', {
                'application': application,
            })

        except Exception as e:
            _logger.exception("Error submitting B2B application: %s", e)
            return request.render('theme_alan.application_error_template', {
                'error_message': 'An unexpected error occurred while submitting your application. Please try again later.',
                'error_title': 'Submission Error'
            })