from odoo import api, fields, models

from .res_partner import PARAM_BASE, PARAM_WINDOW

CRON_XMLID = 'pg_b2b_grade_auto.cron_pg_b2b_grade_auto'

# Periodicidade em linguagem de negócio -> (intervalo, unidade) do ir.cron.
# Não se inventa agendador nenhum: isto só traduz para os campos do standard.
PERIODICIDADES = {
    'daily': (1, 'days'),
    'weekly': (1, 'weeks'),
    'biweekly': (2, 'weeks'),
    'monthly': (1, 'months'),
    'quarterly': (3, 'months'),
    'semiannual': (6, 'months'),
    'annual': (12, 'months'),
}
PERIODICIDADE_INVERSA = {valor: chave for chave, valor in PERIODICIDADES.items()}


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pg_grade_window_months = fields.Integer(
        string="Meses considerados no escalão",
        config_parameter=PARAM_WINDOW,
        help="Quantos meses contam para o escalão.\n"
             "A 0 conta o histórico completo — e nesse caso ninguém desce de"
             " escalão, porque um acumulado nunca diminui.\n"
             "A 12, o escalão acompanha o volume do último ano e pode subir ou"
             " descer.",
    )
    pg_grade_base = fields.Selection(
        selection=[
            ('invoiced', "Faturas emitidas"),
            ('ordered', "Encomendas confirmadas"),
        ],
        string="O escalão conta a partir de",
        default='invoiced',
        config_parameter=PARAM_BASE,
        help="Faturas emitidas: conta o que já foi facturado e lançado, com as"
             " notas de crédito a subtrair.\n"
             "Encomendas confirmadas: conta a venda logo na confirmação, ainda"
             " antes de facturar — era o critério da versão anterior.",
    )

    # --- agendamento: espelho dos campos do ir.cron standard --------------
    pg_grade_cron_active = fields.Boolean(
        string="Apurar o escalão automaticamente",
        help="Enquanto estiver desligado, o escalão só muda à mão ou pela acção"
             " 'B2B: recalcular escalão por faturação'.",
    )
    pg_grade_cron_frequency = fields.Selection(
        selection=[
            ('daily', "Diária"),
            ('weekly', "Semanal"),
            ('biweekly', "Quinzenal"),
            ('monthly', "Mensal"),
            ('quarterly', "Trimestral"),
            ('semiannual', "Semestral"),
            ('annual', "Anual"),
        ],
        string="Periodicidade do apuramento",
    )
    pg_grade_cron_nextcall = fields.Datetime(
        string="Próximo apuramento",
        help="Data e hora do próximo apuramento; é ela que fixa o dia do ciclo."
             " Para apurar no dia 1 de cada mês, pôr aqui um dia 1 e escolher"
             " periodicidade mensal.",
    )

    def _pg_cron(self):
        return self.env.ref(CRON_XMLID, raise_if_not_found=False)

    @api.model
    def get_values(self):
        valores = super().get_values()
        cron = self._pg_cron()
        if cron:
            valores.update(
                pg_grade_cron_active=cron.active,
                pg_grade_cron_frequency=PERIODICIDADE_INVERSA.get(
                    (cron.interval_number, cron.interval_type)),
                pg_grade_cron_nextcall=cron.nextcall,
            )
        return valores

    def set_values(self):
        super().set_values()
        cron = self._pg_cron()
        if not cron:
            return
        vals = {'active': self.pg_grade_cron_active}
        if self.pg_grade_cron_frequency:
            intervalo, unidade = PERIODICIDADES[self.pg_grade_cron_frequency]
            vals.update(interval_number=intervalo, interval_type=unidade)
        if self.pg_grade_cron_nextcall:
            vals['nextcall'] = self.pg_grade_cron_nextcall
        # sudo: quem configura vendas não tem, por norma, escrita em acções
        # planeadas, que é um modelo técnico.
        cron.sudo().write(vals)
