"""Purga o metadado orfao dos modelos removidos na simplificacao a 3 pilares.

O Odoo nem sempre remove os registos ir.model de um modelo que o modulo deixou
de definir (sobretudo quando a tabela ainda tem dados). Esta migracao remove os
vestigios (ir.model + campos + tabela) para que Tecnico > Modelos e a base de
dados reflitam o modulo simplificado. Filtro defensivo: so remove modelos que
NAO estao no registry (classe nao carregada) - nunca toca em modelos ativos.
"""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

REMOVED_MODELS = [
    'pg.project.decisions.sync.run',
    'pg.project.risks.sync.run',
    'pg.project.deliveries.sync.run',
    'pg.project.requirements.sync.run',
    'pg.project.plan.sync.run',
    'pg.project.budget.sync.run',
    'pg.project.budget.line',
    'pg.project.risk',
    'pg.project.status.sync.run',
    'pg.project.chatter.signal',
    'pg.operational.dashboard',
    'project.task.ai.history',
    'project.task.consultive.decision',
]


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    orphans = env['ir.model'].search([('model', 'in', REMOVED_MODELS)]).filtered(
        lambda rec: rec.model not in env
    )
    if not orphans:
        _logger.info("pg_brodoo 1.6.1: sem modelos orfaos a remover.")
        return
    labels = orphans.mapped('model')
    orphans.unlink()
    _logger.info("pg_brodoo 1.6.1: removidos %s modelos orfaos: %s", len(labels), labels)
