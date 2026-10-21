"""Ajuste da limpeza de sessoes para usar o mesmo limite configurado no cookie."""
from odoo import models
from odoo import http

from ..session_patch import get_session_max_inactivity


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def _gc_sessions(self):
        http.root.session_store.vacuum(
            max_lifetime=get_session_max_inactivity(self.env)
        )
