# -*- coding: utf-8 -*-
"""Alertas de entrega na Venda: atividades a 15/7/1 dias da data prevista.

Enquanto a venda nao estiver totalmente faturada, cria uma atividade na
propria Venda a 15, 7 e 1 dia(s) antes da ``commitment_date`` (Data de
Entrega), para os utilizadores configurados no parametro do sistema
``pg_alerta_entrega.user_ids``.
"""
from datetime import timedelta

from odoo import api, fields, models

# Dias antes da data de entrega em que se cria o alerta.
_PG_ALERTA_DIAS = (15, 7, 1)
# Parametro do sistema com os IDs dos utilizadores destinatarios.
_PG_PARAM_USERS = 'pg_alerta_entrega.user_ids'
_PG_PARAM_USERS_DEFAULT = '6,11'


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _pg_alerta_entrega_users(self):
        """Utilizadores destinatarios dos alertas (internos ativos).

        Le os IDs do parametro do sistema ``pg_alerta_entrega.user_ids``
        (lista separada por virgulas) e mantem apenas utilizadores que
        existem, estao ativos e nao sao partilhados (internos).
        """
        param = self.env['ir.config_parameter'].sudo().get_param(
            _PG_PARAM_USERS, _PG_PARAM_USERS_DEFAULT
        ) or ''
        ids = [int(tok) for tok in param.replace(';', ',').split(',') if tok.strip().isdigit()]
        users = self.env['res.users'].browse(ids).exists()
        return users.filtered(lambda u: u.active and not u.share)

    @api.model
    def _pg_cron_alertas_entrega(self):
        """Ponto de entrada da acao agendada (diaria).

        Percorre as vendas confirmadas, ainda nao totalmente faturadas e
        com Data de Entrega definida; quando faltam 15/7/1 dias, agenda uma
        atividade por utilizador destinatario (sem duplicar).
        """
        users = self._pg_alerta_entrega_users()
        if not users:
            return

        today = fields.Date.context_today(self)
        orders = self.search([
            ('state', '=', 'sale'),
            ('invoice_status', '!=', 'invoiced'),
            ('commitment_date', '!=', False),
        ])
        Activity = self.env['mail.activity']

        for order in orders:
            # Data de entrega no fuso do utilizador da acao agendada.
            entrega = fields.Datetime.context_timestamp(
                order, order.commitment_date
            ).date()
            dias_faltam = (entrega - today).days
            if dias_faltam not in _PG_ALERTA_DIAS:
                continue

            data_txt = entrega.strftime('%d/%m/%Y')
            for user in users:
                resumo = "Alerta de entrega: faltam %s dia(s)" % dias_faltam
                # Anti-duplicados: mesmo resumo, mesma venda, mesmo utilizador.
                existe = Activity.search_count([
                    ('res_model', '=', 'sale.order'),
                    ('res_id', '=', order.id),
                    ('user_id', '=', user.id),
                    ('summary', '=', resumo),
                ])
                if existe:
                    continue
                nota = (
                    "Faltam %s dia(s) para a Data de Entrega prevista (%s) "
                    "da venda %s. A venda ainda nao esta totalmente faturada."
                    % (dias_faltam, data_txt, order.name)
                )
                order.activity_schedule(
                    'mail.mail_activity_data_todo',
                    date_deadline=today,
                    summary=resumo,
                    note=nota,
                    user_id=user.id,
                )
