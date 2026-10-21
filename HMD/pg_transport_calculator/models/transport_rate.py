# -*- coding: utf-8 -*-
"""Tarifa de transporte por destino e respetivos escaloes de peso.

`pg.transport.rate` representa uma linha pais/zona de uma transportadora
(equivalente a um item de ``destinations`` no JSON da ferramenta online),
com um valor minimo e varios escaloes (`pg.transport.rate.tier`).

O calculo de custo replica `js/calculator.js`:
  - escalao "flat" (ex.: nacional 1-50 / 51-100): custo = preco do escalao;
  - restantes escaloes: custo = ceil(peso/100) * preco, com limites
    opcionais de minimo (``scale_floor``) e maximo (``scale_cap``) ao
    multiplicador;
  - internacional usa o mesmo ceil(peso/100) (= peso arredondado / 100);
  - custo final nunca inferior ao ``minimum`` do destino.
"""

import math

from odoo import api, fields, models


class TransportRate(models.Model):
    _name = "pg.transport.rate"
    _description = "Tarifa de transporte por destino"
    _order = "carrier_id, country_name, zone_code"
    _rec_name = "display_name"

    carrier_id = fields.Many2one(
        "pg.transport.carrier", required=True, ondelete="cascade", index=True
    )
    carrier_type = fields.Selection(related="carrier_id.carrier_type", store=True)
    country_name = fields.Char(required=True, index=True)
    zone_code = fields.Char(string="Zona", required=True, index=True)
    minimum = fields.Float(string="Minimo", help="Custo minimo cobrado para o destino.")
    tier_ids = fields.One2many("pg.transport.rate.tier", "rate_id", string="Escaloes")
    company_id = fields.Many2one(related="carrier_id.company_id", store=True)
    display_name = fields.Char(compute="_compute_display_name", store=True)

    @api.depends("carrier_id.name", "country_name", "zone_code")
    def _compute_display_name(self):
        for rate in self:
            rate.display_name = "%s / %s / %s" % (
                rate.carrier_id.name or "",
                rate.country_name or "",
                rate.zone_code or "",
            )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._ensure_zones()
        return records

    def write(self, vals):
        res = super().write(vals)
        if "country_name" in vals or "zone_code" in vals:
            self._ensure_zones()
        return res

    def _ensure_zones(self):
        """Garante que existe a zona (pais/codigo) para o dropdown dependente."""
        Zone = self.env["pg.transport.zone"].sudo()
        for rate in self:
            if not rate.country_name or not rate.zone_code:
                continue
            if not Zone.search_count([
                ("country_name", "=", rate.country_name),
                ("code", "=", rate.zone_code),
            ]):
                Zone.create({
                    "country_name": rate.country_name,
                    "code": rate.zone_code,
                })

    def _find_tier(self, weight):
        """Escalao cujo limite superior cobre o peso (ascendente).

        O ultimo escalao (``weight_to == 0``) e aberto (>maximo).
        """
        self.ensure_one()
        tiers = self.tier_ids.sorted(lambda t: (t.sequence, t.weight_to or 1e12))
        for tier in tiers:
            if not tier.weight_to or weight <= tier.weight_to:
                return tier
        return tiers[-1:] and tiers[-1] or self.env["pg.transport.rate.tier"]

    def _compute_cost(self, weight):
        self.ensure_one()
        tier = self._find_tier(weight)
        if not tier:
            return {
                "tier": self.env["pg.transport.rate.tier"],
                "rate_label": False,
                "rate_value": 0.0,
                "scaled_weight": 0.0,
                "cost": self.minimum or 0.0,
                "error": "Sem escalao definido para o destino.",
            }
        if tier.flat:
            scaled = 1.0
            cost = tier.price
        else:
            scaled = math.ceil(weight / 100.0) if weight > 0 else 0.0
            if tier.scale_floor:
                scaled = max(scaled, tier.scale_floor)
            if tier.scale_cap:
                scaled = min(scaled, tier.scale_cap)
            cost = scaled * tier.price
        if cost < (self.minimum or 0.0):
            cost = self.minimum or 0.0
        return {
            "tier": tier,
            "rate_label": tier.code,
            "rate_value": tier.price,
            "scaled_weight": scaled,
            "cost": cost,
            "error": False,
        }


class TransportZone(models.Model):
    _name = "pg.transport.zone"
    _description = "Zona de transporte (por país)"
    _order = "country_name, code"
    _rec_name = "display_name"

    country_name = fields.Char(string="País", required=True, index=True)
    code = fields.Char(string="Zona", required=True, index=True)
    display_name = fields.Char(compute="_compute_display_name", store=True)

    _sql_constraints = [
        ("country_code_uniq", "unique(country_name, code)",
         "Já existe esta zona para o país."),
    ]

    @api.depends("country_name", "code")
    def _compute_display_name(self):
        for zone in self:
            zone.display_name = "%s / %s" % (zone.country_name or "", zone.code or "")


class TransportWarning(models.Model):
    _name = "pg.transport.warning"
    _description = "Aviso/regra de transporte (configurável)"
    _order = "sequence, id"

    name = fields.Char(string="Descrição", required=True)
    text = fields.Text(
        string="Mensagem", required=True,
        help="Texto mostrado no resultado do cálculo quando o aviso aplica.",
    )
    level = fields.Selection(
        selection=[("info", "Informação"), ("warning", "Aviso"), ("error", "Aviso forte")],
        default="warning", required=True,
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    carrier_id = fields.Many2one(
        "pg.transport.carrier", string="Transportadora",
        help="Vazio = aplica a todas as transportadoras.",
    )
    country_name = fields.Char(string="País", help="Vazio = aplica a todos os países.")
    zone_code = fields.Char(string="Zona", help="Vazio = aplica a todas as zonas.")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)


class TransportRateTier(models.Model):
    _name = "pg.transport.rate.tier"
    _description = "Escalao de peso de tarifa de transporte"
    _order = "rate_id, sequence, weight_to"

    rate_id = fields.Many2one(
        "pg.transport.rate", required=True, ondelete="cascade", index=True
    )
    sequence = fields.Integer(default=10)
    code = fields.Char(string="Escalao", required=True, help="Etiqueta do escalao (ex.: 101-200).")
    weight_from = fields.Float(string="Peso de")
    weight_to = fields.Float(
        string="Peso ate",
        help="Limite superior do escalao (kg). 0 = escalao aberto (sem limite).",
    )
    price = fields.Float(string="Preco", help="Preco por unidade tarifaria do escalao.")
    flat = fields.Boolean(
        string="Fixo",
        help="Se marcado, custo = preco (independente do peso). Usado em "
        "escaloes baixos nacionais (1-50, 51-100).",
    )
    scale_floor = fields.Integer(
        string="Mult. minimo",
        help="Limite inferior do multiplicador ceil(peso/100). 0 = sem limite.",
    )
    scale_cap = fields.Integer(
        string="Mult. maximo",
        help="Limite superior do multiplicador ceil(peso/100). 0 = sem limite.",
    )
