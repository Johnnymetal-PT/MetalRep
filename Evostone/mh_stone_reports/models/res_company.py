import base64
import math
from io import BytesIO

from odoo import fields, models

import barcode as barcode_lib
from barcode.writer import ImageWriter
from PIL import Image

# GRF pré-calculado do logo ST (50x40px) - fallback quando não há sticker_logo
DEFAULT_LOGO_GRF = {
    'total': 280,
    'width': 7,
    'hex': (
        '00000000000000000000000000000000000000000000000000000000'
        '000B6DB0DB6D00000FFFF9FFFF80000FFFF8FFFF00000FFFF9FFFF8'
        '0000FFFF8FFFF00000FFFF9FFFF80000FFFF8FFFF00000FFFF9FFFF8'
        '0000FFFF8FFFF00000FFFF9FFFF80000FFFF8FFFF00000FFFF9FFFF8'
        '0000FFF00FFE000000FFF01FFF000000FFF00FFE000000FFF01FFF00'
        '0000FFF00FFE000000FFF01FFF000009FFF00FFE00001FFFF01FFF00'
        '001FFFF00FFE00001FFFF01FFF00001FFFF00FFE00001FFFF01FFF00'
        '001FFFF00FFE00001FFFF01FFF00001FFFF00FFE00001FFFF01FFF00'
        '0008888000040000000000000000000000000000000000000000000'
        '000000000000000000000000'
    ),
}


class ResCompany(models.Model):
    _inherit = 'res.company'

    report_watermark = fields.Binary(
        string='Watermark do Relatório',
        help='Imagem de fundo (watermark) para os relatórios PDF. '
             'Recomenda-se uma imagem PNG com transparência.'
    )

    sticker_logo = fields.Binary(
        string='Logo para Stickers',
        help='Logo usado nos stickers/etiquetas de pedras. '
             'Recomenda-se uma imagem PNG.'
    )

    logo_report = fields.Binary(
        string='Logo para Relatórios',
        help='Logo usado nos relatórios PDF. '
             'Recomenda-se uma imagem PNG.'
    )
    
    mh_bank_ids = fields.One2many(
        'mh.bank', 'company_id', string='Bancos',
        help='Contas bancárias da empresa para exibir nos relatórios.'
    )

    def get_sticker_logo_grf(self, grf_width=50, grf_height=40):
        """Converte sticker_logo (Binary PNG) para formato GRF hex para ZPL.

        Returns:
            dict com 'total' (total bytes), 'width' (bytes/row), 'hex' (hex string)
        """
        self.ensure_one()
        if not self.sticker_logo:
            return DEFAULT_LOGO_GRF

        img_data = base64.b64decode(self.sticker_logo)
        img = Image.open(BytesIO(img_data))
        img = img.resize((grf_width, grf_height), Image.LANCZOS)
        img = img.convert('1')

        width_bytes = math.ceil(img.width / 8)
        total_bytes = width_bytes * img.height
        hex_data = ''

        for y in range(img.height):
            for x_byte in range(width_bytes):
                byte_val = 0
                for bit in range(8):
                    x = x_byte * 8 + bit
                    if x < img.width:
                        pixel = img.getpixel((x, y))
                        if pixel == 0:
                            byte_val |= (1 << (7 - bit))
                hex_data += format(byte_val, '02X')

        return {
            'total': total_bytes,
            'width': width_bytes,
            'hex': hex_data,
        }


def _imagem_para_grf(img):
    """Converte imagem PIL (modo '1') para dados GRF hex."""
    width_bytes = math.ceil(img.width / 8)
    total_bytes = width_bytes * img.height
    hex_data = ''
    for y in range(img.height):
        for x_byte in range(width_bytes):
            byte_val = 0
            for bit in range(8):
                x = x_byte * 8 + bit
                if x < img.width:
                    pixel = img.getpixel((x, y))
                    if pixel == 0:
                        byte_val |= (1 << (7 - bit))
            hex_data += format(byte_val, '02X')
    return {'total': total_bytes, 'width': width_bytes, 'hex': hex_data}


def barcode_to_grf(texto, largura=400, altura=55):
    """Gera barcode Code128 como GRF com largura exacta em dots.

    Args:
        texto: Texto a codificar no barcode
        largura: Largura em dots (default 400 = FO200 até FO600)
        altura: Altura em dots (default 55)

    Returns:
        dict com 'total', 'width', 'hex'
    """
    code128 = barcode_lib.get('code128', texto, writer=ImageWriter())
    img = code128.render({
        'module_width': 0.3,
        'module_height': 8,
        'quiet_zone': 1,
        'write_text': False,
    })
    img = img.convert('L')
    img = img.resize((largura, altura), Image.LANCZOS)
    img = img.convert('1')
    return _imagem_para_grf(img)
