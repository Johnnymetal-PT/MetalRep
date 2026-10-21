# -*- coding: utf-8 -*-
"""Wizard de calculo e comparacao de transporte.

Replica a calculadora online HMD dentro do orcamento:
  1. o utilizador introduz pais/zona e as embalagens (caixas/paletes);
  2. ``action_calculate`` calcula o custo em TODAS as transportadoras que
     servem o destino (comparacao multi-transportadora);
  3. o utilizador escolhe uma linha de resultado e ``Aplicar`` escreve o
     custo no ``price_unit`` da linha de venda do produto de transporte.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import formatLang


class TransportCalculatorWizard(models.TransientModel):
    _name = "pg.transport.calculator.wizard"
    _description = "Calculadora de Transporte"

    order_id = fields.Many2one("sale.order", required=True, readonly=True)
    company_id = fields.Many2one(related="order_id.company_id")
    currency_id = fields.Many2one(related="order_id.currency_id")
    country_name = fields.Selection(
        selection="_selection_country", string="País", required=True
    )
    zone_id = fields.Many2one(
        "pg.transport.zone",
        string="Zona",
        required=True,
        domain="[('country_name', '=', country_name)]",
        help="Zonas disponíveis para o país escolhido.",
    )
    target_line_id = fields.Many2one(
        "sale.order.line",
        string="Linha de Transporte",
        domain="[('order_id', '=', order_id), ('display_type', '=', False)]",
        help="Linha de venda onde o valor de transporte sera aplicado.",
    )
    fuel_surcharge = fields.Float(
        string="Sobretaxa Combustível (%)",
        help="Percentagem sobre o custo base (alguns transportadores aplicam).",
    )
    client_margin = fields.Float(
        related="company_id.pg_transport_client_margin", string="Margem Cliente (%)",
    )
    pallet_fee = fields.Float(
        related="company_id.pg_transport_pallet_fee", string="Valor/Palete (€)",
    )
    package_line_ids = fields.One2many(
        "pg.transport.calculator.package", "wizard_id", string="Embalagens"
    )
    result_line_ids = fields.One2many(
        "pg.transport.calculator.result", "wizard_id", string="Resultados"
    )
    info = fields.Char(readonly=True)

    @api.model
    def _selection_country(self):
        zones = self.env["pg.transport.zone"].search([])
        names = sorted({z.country_name for z in zones if z.country_name})
        return [(n, n) for n in names]

    @api.onchange("country_name")
    def _onchange_country_name(self):
        if self.zone_id and self.zone_id.country_name != self.country_name:
            self.zone_id = False

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        order = self.env["sale.order"].browse(res.get("order_id"))
        if order:
            if "fuel_surcharge" in fields_list and not res.get("fuel_surcharge"):
                res["fuel_surcharge"] = order.company_id.pg_transport_fuel_surcharge
            if "target_line_id" in fields_list and order.pg_transport_line_id:
                res.setdefault("target_line_id", order.pg_transport_line_id.id)
            # recupera o ultimo calculo guardado no orcamento
            if "country_name" in fields_list and order.pg_transport_country:
                res["country_name"] = order.pg_transport_country
            if "zone_id" in fields_list and order.pg_transport_country and order.pg_transport_zone:
                zone = self.env["pg.transport.zone"].search([
                    ("country_name", "=", order.pg_transport_country),
                    ("code", "=", order.pg_transport_zone),
                ], limit=1)
                if zone:
                    res["zone_id"] = zone.id
            if "package_line_ids" in fields_list:
                if order.pg_transport_package_ids:
                    res["package_line_ids"] = [
                        (0, 0, {
                            "package_type": p.package_type,
                            "width": p.width,
                            "length": p.length,
                            "height": p.height,
                            "quantity": p.quantity,
                        })
                        for p in order.pg_transport_package_ids
                    ]
                elif not res.get("package_line_ids"):
                    res["package_line_ids"] = [
                        (0, 0, {"package_type": "box", "quantity": 1})
                    ]
        # valida country default contra a selecao
        if res.get("country_name"):
            valid = dict(self._selection_country())
            if res["country_name"] not in valid:
                res["country_name"] = False
        return res

    def _persist_inputs(self):
        """Guarda os inputs (pais, zona, embalagens) no orcamento."""
        self.ensure_one()
        order = self.order_id
        if not order:
            return
        commands = [(5, 0, 0)]
        seq = 10
        for p in self.package_line_ids:
            commands.append((0, 0, {
                "sequence": seq,
                "package_type": p.package_type,
                "width": p.width,
                "length": p.length,
                "height": p.height,
                "quantity": p.quantity,
            }))
            seq += 10
        order.write({
            "pg_transport_country": self.country_name or False,
            "pg_transport_zone": self.zone_id.code or False,
            "pg_transport_package_ids": commands,
        })

    def action_calculate(self):
        self.ensure_one()
        if not self.package_line_ids:
            raise UserError(_("Adicione pelo menos uma embalagem."))
        packages = [
            {
                "type": p.package_type,
                "width": p.width,
                "length": p.length,
                "height": p.height,
                "quantity": p.quantity,
            }
            for p in self.package_line_ids
        ]
        self._persist_inputs()
        carriers = self.env["pg.transport.carrier"].search(
            [("company_id", "in", [self.company_id.id, False])]
        )
        self.result_line_ids.unlink()
        results = []
        # parametros da cadeia de preco
        surcharge = self.fuel_surcharge or 0.0
        margin = self.company_id.pg_transport_client_margin or 0.0
        pallet_fee = self.company_id.pg_transport_pallet_fee or 0.0
        n_pallets = sum(
            p.quantity for p in self.package_line_ids if p.package_type == "pallet"
        )

        zone_code = self.zone_id.code
        for carrier in carriers:
            quote = carrier.quote(self.country_name, zone_code, packages)
            if not quote:
                continue
            err = quote.get("error")
            msgs = list(quote.get("messages") or [])
            if err:
                msgs = [err] + msgs
                base = operational = client_value = pallet_total = final = 0.0
            else:
                base = quote.get("cost", 0.0)
                operational = base * (1.0 + surcharge / 100.0)
                client_value = operational * (1.0 + margin / 100.0)
                pallet_total = n_pallets * pallet_fee
                final = client_value + pallet_total
            results.append(
                (0, 0, {
                    "carrier_id": carrier.id,
                    "mode": quote["mode"],
                    "total_m3": quote["total_m3"],
                    "total_ldm": quote["total_ldm"],
                    "total_weight": quote["weight"],
                    "scaled_weight": quote.get("scaled_weight", 0.0),
                    "rate_label": quote.get("rate_label") or "",
                    "rate_value": quote.get("rate_value", 0.0),
                    "cost": base,
                    "fuel_surcharge_pct": surcharge,
                    "operational_cost": operational,
                    "client_value": client_value,
                    "pallet_total": pallet_total,
                    "final_value": final,
                    "messages": "\n".join(msgs),
                    "has_error": bool(err),
                })
            )
        if not results:
            raise UserError(
                _("Nenhuma transportadora serve o destino %s / %s.")
                % (self.country_name, self.zone_id.code)
            )
        # erros por ultimo; entre validos, ordena por valor final e marca o mais barato
        results.sort(key=lambda r: (r[2]["has_error"], r[2]["final_value"] if not r[2]["has_error"] else 0.0))
        for res in results:
            if not res[2]["has_error"]:
                res[2]["is_cheapest"] = True
                break
        self.result_line_ids = results
        valid = sum(1 for r in results if not r[2]["has_error"])
        self.info = _("%s transportadora(s) calculada(s); %s com custo válido.") % (len(results), valid)
        return self._reopen()

    def _reopen(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def _apply_cost(self, result):
        self.ensure_one()
        line = self.target_line_id
        if not line:
            raise UserError(
                _("Defina a linha de transporte. Sugestao: configure o "
                  "produto de transporte em Definicoes de Vendas e adicione-o "
                  "ao orcamento.")
            )
        self._persist_inputs()
        # A linha de venda reflete o VALOR TOTAL (custo + sobretaxa +
        # margem + paletes).
        line.write({"price_unit": result.final_value})
        self._fill_logistics_fields(result)
        return {"type": "ir.actions.act_window_close"}

    def _fill_logistics_fields(self, result):
        """Auto-preenche os campos de logistica da venda.

        Regra de negocio (pedido HMD): a aba Logistics separa o custo base
        do resto da cadeia de preco.
          - x_studio_valor_oramento (monetary) <- CUSTO BASE do transporte
            (so o custo da transportadora, sem sobretaxa, margem ou paletes)
          - pg_transport_logistics_notes (text) <- sobretaxa + custo paletes
          - x_studio_transportador (many2one res.partner) <- carrier.partner_id
          - x_studio_nr_oramento (char)                   <- "Tabela HMD"
        Os campos Studio (x_studio_*) so sao escritos se existirem no modelo
        (resiliente a Studio); pg_transport_logistics_notes e do modulo.
        """
        order = self.order_id
        if not order:
            return
        carrier = result.carrier_id
        surcharge_amount = result.operational_cost - result.cost
        n_pallets = sum(
            p.quantity for p in self.package_line_ids if p.package_type == "pallet"
        )
        pallet_fee = self.company_id.pg_transport_pallet_fee or 0.0
        field_map = {
            # apenas o custo base do transporte
            "x_studio_valor_oramento": result.cost,
            "x_studio_nr_oramento": "Tabela HMD",
            "pg_transport_logistics_notes": self._build_logistics_notes(
                result.fuel_surcharge_pct, surcharge_amount,
                n_pallets, pallet_fee, result.pallet_total,
            ),
        }
        if carrier and carrier.partner_id:
            field_map["x_studio_transportador"] = carrier.partner_id.id
        vals = {
            fname: fval
            for fname, fval in field_map.items()
            if fname in order._fields
        }
        if vals:
            order.write(vals)

    def _build_logistics_notes(self, surcharge_pct, surcharge_amount,
                               n_pallets, pallet_fee, pallet_total):
        """Texto de observacoes com os componentes fora do custo base."""
        currency = self.currency_id
        parts = []
        if surcharge_pct or surcharge_amount:
            parts.append(
                _("Sobretaxa combustível: %(pct)s%% (%(amount)s)") % {
                    "pct": ("%g" % (surcharge_pct or 0.0)),
                    "amount": formatLang(
                        self.env, surcharge_amount, currency_obj=currency
                    ),
                }
            )
        if n_pallets:
            parts.append(
                _("Paletes: %(n)s × %(fee)s = %(total)s") % {
                    "n": ("%g" % n_pallets),
                    "fee": formatLang(self.env, pallet_fee, currency_obj=currency),
                    "total": formatLang(
                        self.env, pallet_total, currency_obj=currency
                    ),
                }
            )
        return "\n".join(parts)


class TransportCalculatorPackage(models.TransientModel):
    _name = "pg.transport.calculator.package"
    _description = "Embalagem (linha da calculadora de transporte)"

    wizard_id = fields.Many2one(
        "pg.transport.calculator.wizard", required=True, ondelete="cascade"
    )
    package_type = fields.Selection(
        selection=[("box", "Caixa"), ("pallet", "Palete")],
        default="box",
        required=True,
        string="Tipo",
    )
    width = fields.Float(string="Largura (cm)")
    length = fields.Float(string="Comprimento (cm)")
    height = fields.Float(string="Altura (cm)")
    quantity = fields.Float(string="Qtd", default=1.0)


class TransportCalculatorResult(models.TransientModel):
    _name = "pg.transport.calculator.result"
    _description = "Resultado por transportadora (calculadora de transporte)"
    _order = "cost"

    wizard_id = fields.Many2one(
        "pg.transport.calculator.wizard", required=True, ondelete="cascade"
    )
    carrier_id = fields.Many2one("pg.transport.carrier", string="Transportadora")
    mode = fields.Selection(
        selection=[("m3", "m3"), ("ldm", "LDM")], string="Base"
    )
    total_m3 = fields.Float(string="Total m3", digits=(16, 3))
    total_ldm = fields.Float(string="Total LDM", digits=(16, 2))
    total_weight = fields.Float(string="Peso (kg)", digits=(16, 2))
    scaled_weight = fields.Float(string="Peso tarifario")
    rate_label = fields.Char(string="Escalao")
    rate_value = fields.Float(string="Valor escalao")
    cost = fields.Float(string="Custo Base")
    fuel_surcharge_pct = fields.Float(string="Sobretaxa (%)")
    operational_cost = fields.Float(string="Custo Operacional")
    client_value = fields.Float(string="Valor Cliente")
    pallet_total = fields.Float(string="Valor Paletes")
    final_value = fields.Float(string="Valor Final")
    currency_id = fields.Many2one(related="wizard_id.currency_id")
    cost_money = fields.Monetary(
        string="Valor Final", compute="_compute_cost_money", currency_field="currency_id"
    )
    is_cheapest = fields.Boolean(string="Mais barata")
    messages = fields.Text(string="Avisos / Notas")
    has_error = fields.Boolean(string="Erro")

    @api.depends("final_value")
    def _compute_cost_money(self):
        for r in self:
            r.cost_money = r.final_value

    def action_apply(self):
        self.ensure_one()
        if self.has_error:
            raise UserError(
                _("Não é possível aplicar: corrija as medidas. %s") % (self.messages or "")
            )
        return self.wizard_id._apply_cost(self)
