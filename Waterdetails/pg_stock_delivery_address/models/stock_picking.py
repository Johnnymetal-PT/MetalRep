from odoo import _, api, fields, models

# Campos de morada da guia -> campos standard de res.partner.
PG_ADDRESS_FIELD_MAP = {
    "pg_delivery_street": "street",
    "pg_delivery_city": "city",
    "pg_delivery_state_id": "state_id",
    "pg_delivery_zip": "zip",
    "pg_delivery_country_id": "country_id",
}


class StockPicking(models.Model):
    _inherit = "stock.picking"

    pg_delivery_street = fields.Char(string="Rua")
    pg_delivery_zip = fields.Char(string="Código Postal")
    pg_delivery_city = fields.Char(string="Cidade")
    pg_delivery_state_id = fields.Many2one(
        "res.country.state",
        string="Distrito",
        domain="[('country_id', '=?', pg_delivery_country_id)]",
    )
    pg_delivery_country_id = fields.Many2one("res.country", string="País")
    pg_delivery_address_id = fields.Many2one(
        "res.partner",
        string="Morada de entrega criada",
        copy=False,
        readonly=True,
        help="Morada de entrega (contacto-filho) materializada a partir dos "
             "campos de morada desta guia.",
    )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _pg_address_vals(self):
        """Devolve os valores de morada a aplicar no res.partner filho."""
        self.ensure_one()
        return {
            partner_field: self[picking_field].id
            if isinstance(self[picking_field], models.BaseModel)
            else (self[picking_field] or False)
            for picking_field, partner_field in PG_ADDRESS_FIELD_MAP.items()
        }

    def _pg_has_address_input(self):
        self.ensure_one()
        return any(self[picking_field] for picking_field in PG_ADDRESS_FIELD_MAP)

    def _pg_sync_delivery_address(self):
        """Materializa/atualiza a morada de entrega e religa-a à guia.

        - Pega no contacto seleccionado (`partner_id`).
        - Cria dentro dele um contacto-filho `type='delivery'` com a morada.
        - Substitui o `partner_id` da guia por essa morada.
        - Em re-gravações, atualiza a mesma morada em vez de criar nova.
        """
        Partner = self.env["res.partner"]
        for picking in self:
            if picking.picking_type_code != "outgoing":
                continue
            if not picking._pg_has_address_input():
                continue

            selected = picking.partner_id
            existing = picking.pg_delivery_address_id

            # Determinar o contacto-mãe (sempre a entidade comercial) e a morada-alvo a (re)utilizar.
            if existing and selected in (existing, existing.parent_id, existing.commercial_partner_id):
                # Estado estável: a guia já aponta para a morada criada
                # (ou ainda para o contacto-mãe). Atualizar a mesma morada.
                parent = existing.commercial_partner_id or existing.parent_id or selected.commercial_partner_id or selected.parent_id or selected
                target = existing
            else:
                # Foi escolhido um contacto diferente -> nova morada nele.
                parent = selected.commercial_partner_id or selected.parent_id or selected
                target = False

            if not parent:
                continue

            address_vals = picking._pg_address_vals()
            if target:
                if target.company_id:
                    address_vals["company_id"] = False
                target.write(address_vals)
                address = target
            else:
                address = Partner.with_context(default_company_id=False).create(dict(
                    address_vals,
                    parent_id=parent.id,
                    company_id=False,
                    type="delivery",
                    name=parent.name or picking.pg_delivery_city or _("Morada de entrega"),
                    pg_picking_delivery_address=True,
                ))

            relink_vals = {}
            if picking.partner_id != address:
                relink_vals["partner_id"] = address.id
            if picking.pg_delivery_address_id != address:
                relink_vals["pg_delivery_address_id"] = address.id
            if relink_vals:
                picking.with_context(pg_skip_address_sync=True).write(relink_vals)

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        pickings = super().create(vals_list)
        if not self.env.context.get("pg_skip_address_sync"):
            pickings._pg_sync_delivery_address()
        return pickings

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get("pg_skip_address_sync"):
            return res
        trigger_fields = set(PG_ADDRESS_FIELD_MAP) | {"partner_id"}
        if trigger_fields.intersection(vals):
            self._pg_sync_delivery_address()
        return res
