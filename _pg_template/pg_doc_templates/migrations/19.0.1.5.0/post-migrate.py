from odoo import api, SUPERUSER_ID

from odoo.addons.pg_doc_templates.hooks import _ensure_templates
from odoo.addons.pg_doc_templates.hooks import _ensure_workspace


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    workspace = _ensure_workspace(env)
    _ensure_templates(env, workspace)

