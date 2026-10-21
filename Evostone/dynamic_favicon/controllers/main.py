import base64
import io
from PIL import Image
from odoo import http
from odoo.http import request
from odoo.tools import image_process

class DynamicFavicon(http.Controller):
    
    @http.route('/web/favicon.ico', type='http', auth='public', website=True)
    def favicon(self, **kwargs):
        """
        Serve favicon based on current company logo or default Odoo favicon
        """
        try:
            company = request.env.company
            
            if company and company.logo:
                favicon_data = self._create_favicon_from_logo(company.logo)
                if favicon_data:
                    headers = [
                        ('Content-Type', 'image/x-icon'),
                        ('Cache-Control', 'public, max-age=86400'),
                    ]
                    return request.make_response(favicon_data, headers)
            
            return request.redirect('/web/static/img/favicon.ico')
            
        except Exception:
            return request.redirect('/web/static/img/favicon.ico')
    
    def _create_favicon_from_logo(self, logo_base64):
        """
        Convert company logo to favicon format
        """
        try:
            logo_data = base64.b64decode(logo_base64)
            
            processed_image = image_process(
                logo_data,
                size=(32, 32),
                crop='center',
                output_format='ICO'
            )
            
            if processed_image:
                return processed_image
            
            img = Image.open(io.BytesIO(logo_data))
            
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            img.thumbnail((32, 32), Image.Resampling.LANCZOS)
            
            favicon_io = io.BytesIO()
            img.save(favicon_io, format='ICO', sizes=[(32, 32)])
            favicon_data = favicon_io.getvalue()
            
            return favicon_data
            
        except Exception:
            return None