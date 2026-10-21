"""Sincronizacao de stock.picking entre PICCOLO e PICCOLO_COMMUNITY.

Replica a guia para a BD destino:
- cria/encontra cliente, picking type, locations e produtos por nome;
- preserva campos Studio ``x_studio_volumes_3``, ``x_studio_peso_kg_1``,
  ``x_studio_cubicagem_1`` (no stock.move) e ``x_studio_zona``
  (no stock.picking);
- confirma a guia replicada quando em draft/waiting/confirmed;
- marca a origem com ``x_studio_community_delivery=True``.

Os campos Studio so existem na BD destino se ``pg_bd_connection_fields``
estiver instalado la.
"""
import logging
import odoo
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    # Estes 3 campos vivem em Studio no PICCOLO; aqui apenas se declaram
    # para que ``pg_bd_connection`` possa escrever sem depender de
    # importar Studio em codigo. (NOTA: tambem existem em
    # pg_bd_connection_fields, instalavel na BD destino.)
    x_studio_volumes_3 = fields.Integer(string="Volumes")
    x_studio_peso_kg_1 = fields.Float(string="Peso (Kg)")
    x_studio_cubicagem_1 = fields.Float(string="Cubicagem")


class StockPicking(models.Model):
    _inherit = "stock.picking"

    x_studio_zona = fields.Many2one("res.country.state", string="Zona")
    # Flag de sync, espelha o x_studio_community do account.move.
    x_studio_community_delivery = fields.Boolean(string="Synced to Community", copy=False)

    def _find_or_create_product(self, second_env, product):
        """Procura produto na BD destino por default_code ou nome.

        Se nao existir, cria com categoria/UoM da destino (fallback
        ao primeiro disponivel se o nome nao bate).
        """
        Product = second_env["product.product"].sudo()

        # default_code e mais discriminativo que name; preferir quando existe.
        if product.default_code:
            domain = [("default_code", "=", product.default_code)]
        else:
            domain = [("name", "=", product.name)]

        target_product = Product.search(domain, limit=1)
        if target_product:
            return target_product

        # Match de categoria por nome; fallback a primeira existente.
        category = second_env["product.category"].sudo().search([("name", "=", product.categ_id.name)], limit=1)
        if not category:
            category = second_env["product.category"].sudo().search([], limit=1)

        # Match de UoM por nome; fallback a primeira existente.
        uom = second_env["uom.uom"].sudo().search([("name", "=", product.uom_id.name)], limit=1)
        if not uom:
            uom = second_env["uom.uom"].sudo().search([], limit=1)

        vals = {
            "name": product.name,
            "default_code": product.default_code,
            "type": product.type,
            "uom_id": uom.id if uom else False,
            "uom_po_id": uom.id if uom else False,
            "categ_id": category.id if category else False,
        }

        return Product.create(vals)

    def _find_picking_type(self, second_env, picking_type):
        """Match picking type por (code + warehouse) com 3 niveis de fallback."""
        PickingType = second_env["stock.picking.type"].sudo()

        # 1) Match exato code + warehouse name.
        domain = [("code", "=", picking_type.code)]
        if picking_type.warehouse_id:
            domain.append(("warehouse_id.name", "=", picking_type.warehouse_id.name))

        target = PickingType.search(domain, limit=1)
        if target:
            return target

        # 2) So pelo code (qualquer warehouse).
        target = PickingType.search([("code", "=", picking_type.code)], limit=1)
        if target:
            return target

        # 3) Primeiro picking type disponivel - ultimo recurso.
        return PickingType.search([], limit=1)

    def _find_location(self, second_env, location):
        """Match por ``complete_name`` (nome composto com hierarquia)."""
        if not location:
            return False
        return second_env["stock.location"].sudo().search(
            [("complete_name", "=", location.complete_name)], limit=1,
        )

    def _find_or_create_zona(self, second_env, zona):
        """Replica a Zona (res.country.state) na destino se nao existir."""
        if not zona:
            return False
        State = second_env["res.country.state"].sudo()
        target = State.search([("name", "=", zona.name)], limit=1)
        if target:
            return target

        # Resolver country na destino por code (ISO2); fallback por name.
        country_id = False
        if zona.country_id:
            country = second_env["res.country"].sudo().search([("code", "=", zona.country_id.code)], limit=1)
            if not country:
                country = second_env["res.country"].sudo().search([("name", "=", zona.country_id.name)], limit=1)
            country_id = country.id if country else False

        return State.create({
            "name": zona.name,
            "country_id": country_id,
        })

    def action_sync_delivery(self):
        """Replica esta guia (stock.picking) para PICCOLO_COMMUNITY."""
        self.ensure_one()
        _logger.info("Starting delivery synchronization for Picking ID: %s", self.id)

        second_db = "PICCOLO_COMMUNITY"

        try:
            registry = odoo.registry(second_db)
            if not registry:
                raise ValueError(f"Registry for database {second_db} not found!")

            with registry.cursor() as cr:
                second_env = api.Environment(cr, self.env.uid, {})

                # Forcar acesso multi-company para evitar bloqueios.
                companies = second_env["res.company"].sudo().search([]).ids
                if not companies:
                    raise ValueError(f"No companies found in database {second_db}")

                second_env = api.Environment(cr, self.env.uid, {
                    "allowed_company_ids": companies,
                    "force_company": companies[0],
                })

                second_env.user_id = second_env["res.users"].browse(self.env.uid).sudo()
                second_env.user_id.sudo().write({
                    "company_ids": [(6, 0, companies)],
                    "company_id": companies[0],
                })

                # Cliente: matching por nome; cria se nao existir.
                customer = second_env["res.partner"].sudo().search([("name", "=", self.partner_id.name)], limit=1)
                if not customer:
                    customer = second_env["res.partner"].sudo().create({
                        "name": self.partner_id.name,
                        "email": self.partner_id.email,
                        "phone": self.partner_id.phone,
                        "street": self.partner_id.street,
                        "city": self.partner_id.city,
                        "zip": self.partner_id.zip,
                        "country_id": self.partner_id.country_id.id if self.partner_id.country_id else False,
                        "vat": self.partner_id.vat,
                        "customer_rank": 1,
                    })

                picking_type = self._find_picking_type(second_env, self.picking_type_id)
                if not picking_type:
                    raise ValueError("No picking type found in community database.")

                # Preferir as locations default do picking_type da destino
                # (consistencia com o fluxo natural); fallback pela
                # location de origem.
                location_src = picking_type.default_location_src_id or self._find_location(second_env, self.location_id)
                location_dest = picking_type.default_location_dest_id or self._find_location(second_env, self.location_dest_id)

                if not location_src or not location_dest:
                    raise ValueError("Could not resolve source/destination locations in community database.")

                # Replicar moves: trata variacoes de field do core
                # (``quantity_done`` em 16.x, ``quantity`` em 17.x) e
                # injeta campos Studio se existirem na destino.
                move_lines = []
                move_model = second_env["stock.move"]
                move_fields = move_model._fields
                for move in self.move_ids_without_package:
                    if "quantity_done" in move._fields:
                        qty_done = move.quantity_done or 0.0
                    elif "quantity" in move._fields:
                        qty_done = move.quantity or 0.0
                    else:
                        qty_done = move.product_uom_qty or 0.0

                    product = self._find_or_create_product(second_env, move.product_id)
                    move_name = move.name or product.name
                    if "description_picking" in move._fields:
                        move_name = move.description_picking or move.name or product.name
                    move_vals = {
                        "name": move_name,
                        "product_id": product.id,
                        "product_uom": product.uom_id.id,
                        "product_uom_qty": move.product_uom_qty or 0.0,
                        "location_id": location_src.id,
                        "location_dest_id": location_dest.id,
                    }
                    if "description_picking" in move_fields:
                        move_vals["description_picking"] = move.name or product.name
                    if "quantity_done" in move_fields:
                        move_vals["quantity_done"] = qty_done or 0.0
                    elif "quantity" in move_fields:
                        move_vals["quantity"] = qty_done or 0.0
                    # Campos Studio - so escreve se existirem na destino
                    # (pg_bd_connection_fields tem de estar instalado).
                    if "x_studio_volumes_3" in move_fields:
                        move_vals["x_studio_volumes_3"] = move.x_studio_volumes_3
                    if "x_studio_peso_kg_1" in move_fields:
                        move_vals["x_studio_peso_kg_1"] = move.x_studio_peso_kg_1
                    if "x_studio_cubicagem_1" in move_fields:
                        move_vals["x_studio_cubicagem_1"] = move.x_studio_cubicagem_1
                    move_lines.append((0, 0, move_vals))

                picking_vals = {
                    "partner_id": customer.id,
                    "origin": self.origin,
                    "scheduled_date": self.scheduled_date,
                    "picking_type_id": picking_type.id,
                    "location_id": location_src.id,
                    "location_dest_id": location_dest.id,
                    "move_ids_without_package": move_lines,
                }
                if "x_studio_zona" in second_env["stock.picking"]._fields:
                    picking_vals["x_studio_zona"] = (
                        self._find_or_create_zona(second_env, self.x_studio_zona).id if self.x_studio_zona else False
                    )

                new_picking = second_env["stock.picking"].sudo().create(picking_vals)

                # Confirma a guia para arrancar o ciclo na destino.
                if new_picking.state in ("draft", "waiting", "confirmed"):
                    new_picking.action_confirm()

                # Flag de sync na origem - permite filtros e relatorios.
                self.sudo().write({"x_studio_community_delivery": True})

                self.message_post(body=_("Delivery successfully synced to Community."))
                return True

        except Exception as e:
            _logger.error("Failed to sync delivery: %s", str(e))
            raise ValueError(_("Failed to sync delivery: %s") % str(e))
