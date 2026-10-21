# -*- coding: utf-8 -*-
"""Planeamento Semanal — modelo real e editável (camada de planeamento administrativo).

Uma linha por semana (campo `semana`, ex.: "2" ou "26-s01"). As encomendas ligam-se
por `pg.planeamento.line.semana_id` (One2many), o que permite EDITAR inline no
formulário semanal sem escrever na origem (SO/MO). Os agregados (previsão, efetivo,
tempos) são somas das linhas. Ver o __manifest__.py.
"""
import re

from odoo import api, fields, models


class PgPlaneamentoSemana(models.Model):
    _name = 'pg.planeamento.semana'
    _description = 'Planeamento Semanal'
    _order = 'semana_num, semana'
    _rec_name = 'semana'

    semana = fields.Char(string='Semana', required=True, index=True)
    semana_num = fields.Integer(
        string='Nº Semana', compute='_compute_semana_num', store=True,
    )
    company_id = fields.Many2one(
        'res.company', string='Empresa',
        compute='_compute_company_id', store=True,
    )
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', readonly=True,
    )
    line_ids = fields.One2many(
        'pg.planeamento.line', 'semana_id', string='Encomendas',
    )
    previsao = fields.Monetary(
        string='Previsão', compute='_compute_aggregates', currency_field='currency_id',
        help='Total previsto receber das encomendas desta semana.',
    )
    efetivo = fields.Monetary(
        string='Efetivo', compute='_compute_aggregates', currency_field='currency_id',
        help='Total já faturado das encomendas desta semana.',
    )
    tempo_corte_costura = fields.Float(
        string='Corte e Costura', compute='_compute_aggregates',
        help='Soma das horas de Corte e Costura das encomendas desta semana.',
    )
    tempo_espuma_estofo = fields.Float(
        string='Espuma e Estofo', compute='_compute_aggregates',
        help='Soma das horas de Espuma e Estofo das encomendas desta semana.',
    )
    tempo_embalagem = fields.Float(
        string='Embalagem', compute='_compute_aggregates',
        help='Soma das horas de Embalagem das encomendas desta semana.',
    )
    horas_pessoa_total = fields.Float(
        string='Horas-pessoa', compute='_compute_aggregates',
        help='Soma das horas-pessoa das encomendas desta semana. Ao contrário dos tempos '
             'acima, que são de relógio, este valor multiplica cada registo de tempo pelo '
             'número de pessoas que o produziu.',
    )

    _sql_constraints = [
        ('semana_uniq', 'unique(semana)', 'Já existe um registo para esta semana.'),
    ]

    @api.depends('semana')
    def _compute_semana_num(self):
        for rec in self:
            numbers = re.findall(r'\d+', rec.semana or '')
            # Último grupo de dígitos: funciona para "2" e para "26-s01".
            rec.semana_num = int(numbers[-1]) if numbers else 0

    @api.depends('line_ids.company_id')
    def _compute_company_id(self):
        for rec in self:
            rec.company_id = rec.line_ids[:1].company_id or self.env.company

    @api.depends('line_ids.total', 'line_ids.total_faturado',
                 'line_ids.tempo_corte_costura', 'line_ids.tempo_espuma_estofo',
                 'line_ids.tempo_embalagem', 'line_ids.horas_pessoa_total')
    def _compute_aggregates(self):
        for rec in self:
            rec.previsao = sum(rec.line_ids.mapped('total'))
            rec.efetivo = sum(rec.line_ids.mapped('total_faturado'))
            rec.tempo_corte_costura = sum(rec.line_ids.mapped('tempo_corte_costura'))
            rec.tempo_espuma_estofo = sum(rec.line_ids.mapped('tempo_espuma_estofo'))
            rec.tempo_embalagem = sum(rec.line_ids.mapped('tempo_embalagem'))
            rec.horas_pessoa_total = sum(rec.line_ids.mapped('horas_pessoa_total'))

    def action_open_lines(self):
        self.ensure_one()
        tree = self.env.ref(
            'pg_planeamento_oficina.view_pg_planeamento_line_semana_tree')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Encomendas da Semana %s' % (self.semana or ''),
            'res_model': 'pg.planeamento.line',
            'domain': [('semana_id', '=', self.id)],
            'view_mode': 'tree,form',
            'views': [(tree.id, 'tree'), (False, 'form')],
            'target': 'current',
        }
