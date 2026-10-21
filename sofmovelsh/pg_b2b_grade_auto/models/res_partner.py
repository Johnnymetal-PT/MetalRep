import logging

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

PARAM_WINDOW = 'pg_b2b_grade_auto.window_months'
DEFAULT_WINDOW = '0'  # 0 = desde sempre

PARAM_BASE = 'pg_b2b_grade_auto.base'
DEFAULT_BASE = 'invoiced'


class ResPartner(models.Model):
    _inherit = 'res.partner'

    pg_grade_auto = fields.Boolean(
        string="Escalão automático",
        default=False,
        help="Só os clientes com esta opção ligada entram no cálculo automático."
             " Quem não a tiver mantém o escalão que lhe for dado à mão.\n"
             "Marcar na empresa, não nos contactos: a faturação é somada por"
             " entidade comercial.",
    )
    pg_invoiced_total = fields.Monetary(
        string="Faturação considerada",
        currency_field='pg_currency_id',
        readonly=True,
        copy=False,
        help="Valor apurado no último cálculo, já sem impostos e descontando"
             " notas de crédito.",
    )
    pg_grade_computed_on = fields.Datetime(
        string="Escalão calculado em",
        readonly=True,
        copy=False,
    )
    pg_currency_id = fields.Many2one(
        comodel_name='res.currency',
        compute='_compute_pg_currency_id',
    )

    @api.depends('company_id')
    def _compute_pg_currency_id(self):
        for partner in self:
            partner.pg_currency_id = (partner.company_id or self.env.company).currency_id

    # ------------------------------------------------------------------
    # Cálculo
    # ------------------------------------------------------------------

    @api.model
    def _pg_window_start(self):
        """Data a partir da qual a faturação conta, ou None para contar tudo.

        Controlado pelo parâmetro `pg_b2b_grade_auto.window_months`. A 0 (por
        omissão) soma o histórico completo, que é o comportamento da V17 — e
        que significa que **ninguém desce de escalão**, porque um acumulado
        nunca diminui. Pôr 12 dá uma janela móvel de um ano, em que o escalão
        acompanha o volume recente nos dois sentidos.
        """
        meses = int(self.env['ir.config_parameter'].sudo().get_param(
            PARAM_WINDOW, DEFAULT_WINDOW) or 0)
        if meses <= 0:
            return None
        return fields.Date.context_today(self) - relativedelta(months=meses)

    @api.model
    def _pg_cron_recompute_grades(self):
        """Ponto de entrada do agendador."""
        return self.search([('pg_grade_auto', '=', True)])._pg_recompute_grades()

    def _pg_recompute_grades(self):
        """Recalcula o escalão dos clientes de `self` a partir da faturação.

        A base é a faturação emitida e lançada, sem impostos, em moeda da
        empresa, com as notas de crédito a subtrair (`amount_untaxed_signed`).
        A soma é por entidade comercial, para que as faturas emitidas a
        contactos da empresa contem para a empresa.

        Escrever `grade_id` faz o `partnership` aplicar a lista de preços do
        escalão. Na descida para "sem escalão" é este método que limpa a lista,
        porque o standard só a aplica quando há escalão.

        :return: número de clientes que mudaram de escalão
        """
        escaloes = self.env['res.partner.grade'].search([('pg_auto_assign', '=', True)])
        if not escaloes:
            _logger.warning(
                "pg_b2b_grade_auto: nenhum escalão marcado como automático; nada a fazer."
            )
            return 0

        # O escalão vive na entidade comercial; contactos filhos são ignorados.
        alvos = self.filtered(lambda p: p.commercial_partner_id == p)
        if len(alvos) != len(self):
            _logger.info(
                "pg_b2b_grade_auto: %s contacto(s) ignorado(s) por não serem entidade comercial.",
                len(self) - len(alvos),
            )
        if not alvos:
            return 0

        totais = self._pg_totals(alvos)

        agora = fields.Datetime.now()
        mudancas = 0
        for parceiro in alvos:
            total = totais.get(parceiro.id, 0.0)
            novo = self._pg_grade_for_amount(escaloes, total)
            vals = {'pg_invoiced_total': total, 'pg_grade_computed_on': agora}

            if novo != parceiro.grade_id:
                anterior = parceiro.grade_id
                vals['grade_id'] = novo.id
                if not novo and anterior.default_pricelist_id and \
                        parceiro.specific_property_product_pricelist == anterior.default_pricelist_id:
                    # Descida para sem escalão: retirar a lista que o escalão
                    # anterior tinha posto, sem tocar em listas atribuídas à mão.
                    vals['specific_property_product_pricelist'] = False
                mudancas += 1
                _logger.info(
                    "pg_b2b_grade_auto: %s (%s) %s -> %s",
                    parceiro.display_name, total,
                    anterior.name or "sem escalão", novo.name or "sem escalão",
                )

            parceiro.write(vals)

        _logger.info(
            "pg_b2b_grade_auto: %s cliente(s) avaliado(s), %s mudança(s) de escalão.",
            len(alvos), mudancas,
        )
        return mudancas

    def _pg_totals(self, alvos):
        """Valor por entidade comercial, segundo a base escolhida nas definições."""
        base = self.env['ir.config_parameter'].sudo().get_param(PARAM_BASE, DEFAULT_BASE)
        inicio = self._pg_window_start()
        if base == 'ordered':
            return self._pg_totals_ordered(alvos, inicio)
        return self._pg_totals_invoiced(alvos, inicio)

    def _pg_totals_invoiced(self, alvos, inicio):
        """Faturas lançadas, sem impostos, em moeda da empresa.

        `amount_untaxed_signed` já traz as notas de crédito com sinal negativo,
        e o agrupamento por entidade comercial junta as faturas emitidas aos
        contactos da empresa.
        """
        dominio = [
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('state', '=', 'posted'),
            ('commercial_partner_id', 'in', alvos.ids),
        ]
        if inicio:
            dominio.append(('invoice_date', '>=', inicio))
        return {
            parceiro.id: total
            for parceiro, total in self.env['account.move']._read_group(
                dominio,
                groupby=['commercial_partner_id'],
                aggregates=['amount_untaxed_signed:sum'],
            )
        }

    def _pg_totals_ordered(self, alvos, inicio):
        """Encomendas confirmadas, sem impostos — o critério da V17.

        A `sale.order` não guarda a entidade comercial, por isso o domínio
        apanha os contactos com `child_of` e a soma é dobrada para a empresa
        aqui. Nota: `amount_untaxed` vem na moeda da encomenda e não é
        convertido — só é exacto em empresa de moeda única, que é o caso.
        """
        dominio = [('state', '=', 'sale'), ('partner_id', 'child_of', alvos.ids)]
        if inicio:
            dominio.append(('date_order', '>=', inicio))
        totais = dict.fromkeys(alvos.ids, 0.0)
        for parceiro, total in self.env['sale.order']._read_group(
            dominio, groupby=['partner_id'], aggregates=['amount_untaxed:sum'],
        ):
            empresa = parceiro.commercial_partner_id.id
            if empresa in totais:
                totais[empresa] += total
        return totais

    @api.model
    def _pg_grade_for_amount(self, escaloes, total):
        """Escalão mais alto cuja faturação mínima já foi atingida."""
        candidatos = escaloes.sorted(key=lambda g: g.pg_min_invoiced, reverse=True)
        for escalao in candidatos:
            if total >= escalao.pg_min_invoiced:
                return escalao
        return self.env['res.partner.grade']

    # ------------------------------------------------------------------
    # Acção manual
    # ------------------------------------------------------------------

    def action_pg_recompute_grade(self):
        """Recalcula agora, para os clientes seleccionados."""
        mudancas = self._pg_recompute_grades()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': _("%(avaliados)s cliente(s) avaliado(s); %(mudancas)s mudaram de escalão.",
                             avaliados=len(self), mudancas=mudancas),
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
