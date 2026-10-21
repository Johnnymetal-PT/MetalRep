# -*- coding: utf-8 -*-
"""Número de pessoas na operação, e sua passagem para cada registo de tempo.

Ver o __manifest__.py para o contexto de negócio.
"""
from odoo import _, api, fields, models
from odoo.exceptions import UserError

# Abaixo deste tempo decorrido, mudar o número é tratado como correcção de lapso e não como
# alteração real da equipa. Ver `pg_set_people_count`.
MINUTOS_LAPSO = 2.0


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    pg_people_count = fields.Integer(
        string="Nº de pessoas",
        default=1,
        copy=False,
        help="Quantas pessoas estão a trabalhar nesta operação. Cada registo de tempo "
             "guarda uma fotografia deste valor no momento em que arranca, pelo que alterar "
             "aqui afecta os registos seguintes e não os anteriores.",
    )

    pg_people_count_needed = fields.Boolean(
        string="Pedir o nº de pessoas",
        compute="_compute_pg_people_count_needed",
        help="Verdadeiro enquanto a operação não tiver nenhum registo de tempo. O Chão de "
             "Fábrica usa-o para saber se tem de perguntar quantas pessoas estão a "
             "trabalhar, o que só acontece à primeira contagem.",
    )

    pg_person_hours = fields.Float(
        string="Horas-pessoa",
        compute="_compute_pg_person_hours",
        help="Soma das horas-pessoa de todos os registos de tempo desta operação.",
    )

    @api.depends("time_ids")
    def _compute_pg_people_count_needed(self):
        for operacao in self:
            operacao.pg_people_count_needed = not operacao.time_ids

    @api.depends("time_ids.pg_person_hours")
    def _compute_pg_person_hours(self):
        for operacao in self:
            operacao.pg_person_hours = sum(operacao.time_ids.mapped("pg_person_hours"))

    def pg_set_people_count(self, count):
        """Altera o número de pessoas nesta operação, distinguindo dois casos diferentes.

        O pedido "quero mudar o número a meio" esconde duas situações que não se resolvem da
        mesma maneira:

        - **lapso** — indicou-se 4 mas eram 3 desde o início. O tempo já decorrido pertence a
          3 pessoas, logo corrige-se o próprio registo em curso;
        - **alteração real** — eram 4 e alguém saiu. O tempo já decorrido pertence
          efectivamente a 4 pessoas, e só a partir de agora são 3. Reescrever o registo
          falsificaria o passado; o correcto é fechar o registo em curso e abrir outro.

        Distinguem-se pelo tempo decorrido, sem perguntar nada ao operador: até
        `MINUTOS_LAPSO` assume-se lapso, acima disso assume-se alteração real. Um erro de
        digitação é notado em segundos; alguém sair da equipa leva mais tempo do que isso.

        Para correcções retroactivas descobertas muito depois, o caminho é o back office,
        onde o gestor de fabrico edita o registo — reescrever o passado não deve ser uma
        acção de chão de fábrica.
        """
        self.ensure_one()
        try:
            count = int(count)
        except (TypeError, ValueError):
            count = 0
        if count < 1:
            raise UserError(_("O número de pessoas tem de ser pelo menos 1."))

        self.pg_people_count = count
        em_curso = self.time_ids.filtered(lambda t: not t.date_end)
        if not em_curso:
            # Nada a contar: o número fica guardado para a próxima contagem.
            return {"acao": "guardado", "pessoas": count}

        # `duration` só é apurada ao fechar o registo, por isso o tempo decorrido calcula-se
        # a partir do início.
        agora = fields.Datetime.now()
        decorridos = [
            (agora - r.date_start).total_seconds() / 60.0
            for r in em_curso if r.date_start
        ]
        if decorridos and max(decorridos) <= MINUTOS_LAPSO:
            em_curso.pg_people_count = count
            return {"acao": "corrigido", "pessoas": count}

        empregados = em_curso.employee_id
        em_curso._close()
        for empregado in empregados:
            self.start_employee(empregado.id)
        return {"acao": "dividido", "pessoas": count}

    def _prepare_timeline_vals(self, duration, date_start, date_end=False):
        """Marca o registo de tempo com o número de pessoas da operação.

        Este é o ponto único por onde passam os registos de tempo criados a partir do Chão
        de Fábrica: o `button_start` do Enterprise chama `start_employee`
        (`mrp_workorder/models/mrp_workorder.py:288`), que chama este método para montar os
        valores e só depois cria o registo.

        A contagem vem do campo da operação, e não do contexto da chamada. A razão é
        prática: o `startWorking` do Chão de Fábrica constrói o contexto de `button_start`
        internamente, com valores fixos, pelo que acrescentar-lhe uma chave obrigaria a
        reimplementar esse método — código do Enterprise, longo e que muda entre versões.
        Gravar o número na operação antes de arrancar evita isso por completo, e dá de graça
        a alteração a meio da operação: escreve-se o campo e os registos seguintes seguem-no.

        O contexto continua a ser aceite como precedência, por ser útil em chamadas por API
        e em testes.
        """
        vals = super()._prepare_timeline_vals(duration, date_start, date_end=date_end)
        pessoas = self.env.context.get("pg_people_count") or self.pg_people_count
        try:
            pessoas = int(pessoas or 0)
        except (TypeError, ValueError):
            pessoas = 0
        vals["pg_people_count"] = pessoas if pessoas > 0 else 1
        return vals
