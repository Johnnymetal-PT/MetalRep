# -*- coding: utf-8 -*-
"""Transportadora e respetivos fatores de conversao volumetrica.

Cada transportadora ("tabela" na ferramenta online HMD) define os
fatores que convertem volume (m3) ou metros lineares de carga (LDM) em
peso tarifario, e agrega as tarifas por destino (`pg.transport.rate`).

O motor de cubicagem replica fielmente as funcoes
`calcular_xbslog_nacional` / `calcular_xbslog_international` da
calculadora online HMD (versao evoluida, com mensagens):
  - decisao LDM vs m3 + mensagem explicativa do porque;
  - aviso/erro quando paletes altas tem comprimento fora de 100-125;
  - ajuste de palete alta (>125) para altura 250 no calculo por m3
    (o comprimento NAO e ajustado no m3 - so a altura);
  - mensagem de peso tarifario (<=2500 agente local / >2500 direta);
  - avisos configuraveis por destino/tipologia (`pg.transport.warning`).
"""

import math

from odoo import api, fields, models


class TransportCarrier(models.Model):
    _name = "pg.transport.carrier"
    _description = "Transportadora (tabela de tarifas de transporte)"
    _order = "carrier_type, name"

    name = fields.Char(required=True)
    code = fields.Char(
        required=True,
        help="Identificador tecnico unico da tabela (ex.: xbslog_nacional).",
    )
    carrier_type = fields.Selection(
        selection=[("national", "Nacional"), ("international", "Internacional")],
        required=True,
        default="national",
    )
    conv_m3 = fields.Float(
        string="Fator m3 -> kg",
        default=250.0,
        help="Peso tarifario por metro cubico (kg/m3).",
    )
    conv_ldm = fields.Float(
        string="Fator LDM -> kg",
        default=1500.0,
        help="Peso tarifario por metro linear de carga (kg/LDM).",
    )
    active = fields.Boolean(default=True)
    partner_id = fields.Many2one(
        "res.partner",
        string="Parceiro / Contacto",
        help="Parceiro (res.partner) associado a esta transportadora. Usado "
        "para preencher o campo 'Transportador' do separador de logística "
        "da venda ao aplicar o cálculo.",
    )
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company
    )
    rate_ids = fields.One2many(
        "pg.transport.rate", "carrier_id", string="Tarifas por destino"
    )
    rate_count = fields.Integer(compute="_compute_rate_count")
    notes = fields.Text()

    _sql_constraints = [
        ("code_company_uniq", "unique(code, company_id)",
         "O codigo da transportadora tem de ser unico por empresa."),
    ]

    def _compute_rate_count(self):
        data = self.env["pg.transport.rate"]._read_group(
            [("carrier_id", "in", self.ids)], ["carrier_id"], ["__count"]
        )
        mapping = {carrier.id: count for carrier, count in data}
        for carrier in self:
            carrier.rate_count = mapping.get(carrier.id, 0)

    def action_view_rates(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.name,
            "res_model": "pg.transport.rate",
            "view_mode": "list,form",
            "domain": [("carrier_id", "=", self.id)],
            "context": {"default_carrier_id": self.id},
        }

    # ------------------------------------------------------------------
    # Motor de cubicagem (porta das funcoes calcular_xbslog_* evoluidas)
    # ------------------------------------------------------------------
    def _compute_volumetric_weight(self, packages):
        """Calcula o peso tarifario e as mensagens explicativas.

        :param packages: lista de dicts com ``type`` ('box'|'pallet'),
            ``width``, ``length``, ``height`` (cm) e ``quantity``.
        :return: dict com ``mode`` ('ldm'|'m3'), ``total_ldm``,
            ``total_m3``, ``weight`` (kg), ``messages`` (list[str]) e
            ``error`` (str|None - bloqueia o calculo).
        """
        self.ensure_one()
        pkgs = [self._normalize_package(p) for p in packages if p]
        pallets = [p for p in pkgs if p["type"] == "pallet"]
        has_pallet = bool(pallets)
        has_box = any(p["type"] == "box" for p in pkgs)
        only_pallets = has_pallet and len(pallets) == len(pkgs)
        all_pallets_high = has_pallet and all(p["height"] > 125 for p in pallets)
        all_lengths_valid = all(
            100 <= p["length"] <= 125 for p in pallets if p["height"] > 125
        )
        existe_pallet_alta = any(p["height"] > 125 for p in pallets)
        existe_pallet_baixa = any(p["height"] <= 125 for p in pallets)

        messages = []
        total_ldm = 0.0
        total_m3 = 0.0

        # 1. Caso especial LDM: so paletes, todas altas
        if only_pallets and all_pallets_high:
            if not all_lengths_valid:
                return {
                    "mode": "ldm", "total_ldm": 0.0, "total_m3": 0.0,
                    "weight": 0.0, "messages": [],
                    "error": "Palete com o comprimento fora de medida (deve "
                             "estar entre 100 e 125 cm). Não é possível "
                             "calcular por LDM.",
                }
            messages.append(
                "Cálculo feito por LDM porque todas as paletes têm altura "
                "superior a 125 cm e comprimento entre 100 e 125 cm."
            )
            for p in pallets:
                # comprimento sempre considerado 120 (validado 100-125)
                total_ldm += (p["width"] / 240.0) * (120.0 / 100.0) * p["quantity"]
            weight = total_ldm * (self.conv_ldm or 0.0)
            mode = "ldm"
        else:
            # 2. Calculo por m3 (todas as outras situacoes)
            for p in pkgs:
                if p["type"] == "pallet" and p["height"] > 125:
                    adj_h = 250.0  # palete alta forcada a 250 cm
                else:
                    adj_h = p["height"]
                # NOTA: no m3 o comprimento NAO e ajustado (so a altura)
                m3 = (p["width"] * p["length"] * adj_h) / 1_000_000.0
                total_m3 += m3 * p["quantity"]
            weight = total_m3 * (self.conv_m3 or 0.0)
            mode = "m3"
            if existe_pallet_alta and (existe_pallet_baixa or has_box):
                messages.append(
                    "Embora uma ou mais paletes tenham altura superior a "
                    "125 cm, o cálculo foi feito por m³ por haver mistura de "
                    "tipos (paletes altas com paletes baixas e/ou caixas). "
                    "Nestes casos, as paletes altas são consideradas com "
                    "altura de 250 cm."
                )
            elif existe_pallet_baixa and not existe_pallet_alta:
                messages.append(
                    "O cálculo foi feito por m³ porque existem apenas paletes "
                    "baixas (≤ 125 cm) ou caixas."
                )
            elif has_box and not existe_pallet_alta and not existe_pallet_baixa:
                messages.append(
                    "O cálculo foi feito por m³ porque existem caixas nas linhas."
                )
            elif existe_pallet_alta and not existe_pallet_baixa and not has_box:
                messages.append(
                    "O cálculo foi feito por m³ porque as dimensões das "
                    "paletes não permitem o cálculo por LDM."
                )

        return {
            "mode": mode,
            "total_ldm": total_ldm,
            "total_m3": total_m3,
            "weight": weight,
            "messages": messages,
            "error": None,
        }

    @staticmethod
    def _normalize_package(p):
        return {
            "type": p.get("type") or "box",
            "width": float(p.get("width") or 0.0),
            "length": float(p.get("length") or 0.0),
            "height": float(p.get("height") or 0.0),
            "quantity": float(p.get("quantity") or 0.0),
        }

    def _matching_warnings(self, country_name, zone_code):
        """Avisos configuraveis aplicaveis a este destino/transportadora."""
        return self.env["pg.transport.warning"].search([
            ("active", "=", True),
            "|", ("carrier_id", "=", False), ("carrier_id", "=", self.id),
            "|", ("country_name", "=", False), ("country_name", "=", country_name),
            "|", ("zone_code", "=", False), ("zone_code", "=", zone_code),
        ])

    def quote(self, country_name, zone_code, packages):
        """Calcula custo + mensagens para esta transportadora/destino.

        Devolve ``None`` se a transportadora nao serve o destino.
        """
        self.ensure_one()
        rate = self.env["pg.transport.rate"].search([
            ("carrier_id", "=", self.id),
            ("country_name", "=", country_name),
            ("zone_code", "=", zone_code),
        ], limit=1)
        if not rate:
            return None

        vol = self._compute_volumetric_weight(packages)
        messages = list(vol.get("messages") or [])

        if vol.get("error"):
            return {
                "carrier": self, "rate": rate,
                "mode": vol["mode"], "total_ldm": vol["total_ldm"],
                "total_m3": vol["total_m3"], "weight": 0.0,
                "scaled_weight": 0.0, "rate_label": False, "rate_value": 0.0,
                "cost": 0.0, "messages": messages, "error": vol["error"],
            }

        cost = rate._compute_cost(vol["weight"])

        # Mensagem de tipo de entrega por peso tarifario
        rounded = math.ceil(vol["weight"] / 100.0) * 100 if vol["weight"] > 0 else 0
        if rounded <= 2500:
            messages.append(
                "Entrega prevista por agente local (peso tarifário ≤ 2500 kg)."
            )
        elif self.carrier_type == "international":
            messages.append(
                "Valores para entrega direta de carro internacional "
                "(peso tarifário > 2500 kg)."
            )
        else:
            messages.append(
                "Valores para entrega direta (peso tarifário > 2500 kg)."
            )

        # Avisos configuraveis por destino/tipologia
        for warn in self._matching_warnings(country_name, zone_code):
            prefix = "Atenção: " if warn.level in ("warning", "error") else ""
            messages.append(prefix + (warn.text or ""))

        return {
            "carrier": self, "rate": rate,
            "mode": vol["mode"], "total_ldm": vol["total_ldm"],
            "total_m3": vol["total_m3"], "weight": vol["weight"],
            "messages": messages, "error": None, **cost,
        }
