import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Revert do AUD-04: remove o cron de heartbeat do mirror health, que estava a
    gerar commits recorrentes nos repositorios dos projetos. O codigo que publicava
    .pg/MIRROR_HEALTH.json foi removido nesta versao; aqui limpamos o registo de cron
    orfao (data com noupdate=1 nao e apagada automaticamente no upgrade)."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    cron = env.ref('pg_brodoo.ir_cron_pg_project_mirror_health', raise_if_not_found=False)
    if cron:
        cron.unlink()
        _logger.info("pg_brodoo 19.0.1.7.1: cron de mirror health removido (revert AUD-04).")
    else:
        _logger.info("pg_brodoo 19.0.1.7.1: cron de mirror health ja nao existia.")
