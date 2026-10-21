# -*- coding: utf-8 -*-
"""Ponto de entrada para abrir o leitor de QR a partir dos contactos."""
from odoo import models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def action_open_qr_scanner(self):
        # Devolve uma ação cliente; o tag 'open_qr_scanner' está registado no qr_scanner.js,
        # que abre a câmara e trata da leitura/criação do contacto.
        return {
            'type': 'ir.actions.client',
            'tag': 'open_qr_scanner',
        }

