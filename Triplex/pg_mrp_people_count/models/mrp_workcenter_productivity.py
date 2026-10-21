# -*- coding: utf-8 -*-
"""Número de pessoas associado a cada registo de tempo.

Ver o __manifest__.py para o contexto de negócio e para a nota sobre os registos antigos.
"""
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MrpWorkcenterProductivity(models.Model):
    _inherit = "mrp.workcenter.productivity"

    pg_people_count = fields.Integer(
        string="Nº de pessoas",
        default=1,
        help="Quantas pessoas trabalharam durante este registo de tempo. O tempo medido é "
             "de relógio; multiplicado por este número dá as horas-pessoa.",
    )

    pg_person_hours = fields.Float(
        string="Horas-pessoa",
        compute="_compute_pg_person_hours",
        store=True,
        help="Duração do registo multiplicada pelo número de pessoas.",
    )

    @api.depends("duration", "pg_people_count")
    def _compute_pg_person_hours(self):
        for registo in self:
            # `duration` vem em minutos.
            pessoas = registo.pg_people_count or 1
            registo.pg_person_hours = (registo.duration or 0.0) / 60.0 * pessoas

    def write(self, vals):
        """A contagem é alterável até a operação ser marcada como concluída.

        Decidido com o cliente a 28/07/2026: o operador pode corrigir o número de pessoas a
        qualquer momento enquanto a operação estiver em curso, e deixa de poder depois de a
        marcar como concluída — senão o número deixaria de corresponder ao que foi entregue.

        O gestor de fabrico não é travado: uma correcção descoberta depois do fecho continua
        a ser possível no back office, que é onde os erros de registo se corrigem. Travar
        todos criaria um problema de suporte sem resolver nenhum.
        """
        if "pg_people_count" in vals and not self.env.user.has_group("mrp.group_mrp_manager"):
            fechadas = self.filtered(
                lambda r: r.workorder_id.state in ("done", "cancel")
            )
            if fechadas:
                raise UserError(_(
                    "A operação já foi marcada como concluída, pelo que o número de pessoas "
                    "não pode ser alterado. Peça a correcção a um gestor de fabrico."
                ))
        return super().write(vals)
