from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class BaseImport(models.TransientModel):
    _inherit = 'base_import.import'
    
    # Removida a interceptação para permitir o fluxo normal de importação
    # O wizard será acessado através de um botão/menu separado