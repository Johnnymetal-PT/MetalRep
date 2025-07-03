from odoo import http
from odoo.http import request
import vobject
import logging

_logger = logging.getLogger(__name__)

class QRContactController(http.Controller):

    @http.route('/create_partner_from_vcard', type='json', auth='user', csrf=False)
    def create_partner_from_vcard(self, vcard):
        _logger.info("📥 Raw vCard received:\n%s", vcard)

        try:
            card = vobject.readOne(vcard)

            name = getattr(card, 'fn', False).value if hasattr(card, 'fn') else 'Unnamed'
            mobile = None
            email = None
            website = getattr(card, 'url', False)
            street = city = zip_code = country = ''

            # Pick the first cell phone
            for tel in card.contents.get('tel', []):
                types = [t.lower() for t in tel.params.get('TYPE', [])]
                if 'cell' in types:
                    mobile = tel.value
                    break

            # First email
            for mail in card.contents.get('email', []):
                email = mail.value
                break

            # Address
            if hasattr(card, 'adr'):
                adr = card.adr.value
                street = adr.street or ''
                city = adr.city or ''
                zip_code = adr.code or ''
                country = adr.country or ''

            # Company and title
            company = getattr(card, 'org', None)
            company_name = company.value[0] if company else ''
            function = getattr(card, 'title', None)

            parent_id = False
            if company_name:
                existing_company = request.env['res.partner'].sudo().search(
                    [('name', '=', company_name), ('is_company', '=', True)], limit=1
                )
                if existing_company:
                    parent_id = existing_company.id
                else:
                    new_company = request.env['res.partner'].sudo().create({
                        'name': company_name,
                        'is_company': True,
                    })
                    parent_id = new_company.id
                    _logger.info("🏢 Created new company: %s (ID %s)", company_name, parent_id)

            vals = {
                'name': name,
                'mobile': mobile,
                'email': email,
                'website': website.value if website else '',
                'street': street,
                'city': city,
                'zip': zip_code,
                'function': function.value if function else '',
                'parent_id': parent_id,
            }

            _logger.info("📝 Parsed contact values:\n%s", vals)

            partner = request.env['res.partner'].sudo().create(vals)
            _logger.info("✅ Contact created: ID %s (%s)", partner.id, partner.name)

            return {'status': 'success', 'partner_id': partner.id}

        except Exception as e:
            _logger.error("❌ Failed to process vCard: %s", str(e), exc_info=True)
            return {'status': 'error', 'message': f"vCard parsing failed: {e}"}

