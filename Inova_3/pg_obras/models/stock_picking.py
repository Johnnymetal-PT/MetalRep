from odoo import api, models

class StockPicking(models.Model):
    _inherit = "stock.picking"

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------

    def _pg_obras_get_project_distribution(self):
        self.ensure_one()
        if "project_id" not in self._fields or not self.project_id or not getattr(self.project_id, "account_id", False):
            return {}
        return {self.project_id.account_id.id: 100}

    def _pg_obras_get_project_location(self):
        """Destino pretendido: OBR/<cliente>/<projeto> (fallback OBR/<cliente>)"""
        self.ensure_one()

        if "project_id" not in self._fields or not self.project_id:
            return self.env["stock.location"]

        project = self.project_id
        if "x_localizacao_projeto" in project._fields and project.x_localizacao_projeto:
            return project.x_localizacao_projeto

        partner = project.partner_id
        if partner and getattr(partner, "x_localizacao_obra", False):
            return partner.x_localizacao_obra

        return self.env["stock.location"]

    def _pg_obras_get_picking_types(self):
        """
        Resolve os picking types do PG Obras (por XML ID).
        Fallback opcional se ainda não existir xmlid por algum motivo.
        """
        pt_obras_in = self.env.ref("pg_obras.picking_type_obras_in", raise_if_not_found=False)
        pt_eobr = self.env.ref("pg_obras.picking_type_eobr", raise_if_not_found=False)

        # Fallbacks defensivos
        pt_model = self.env["stock.picking.type"].sudo()
        company = self.env.company

        if not pt_obras_in:
            pt_obras_in = pt_model.search([
                ("code", "=", "incoming"),
                ("barcode", "=", "OBRIN"),
                ("company_id", "in", [company.id, False]),
            ], limit=1)

        if not pt_eobr:
            pt_eobr = (
                pt_model.search([
                    ("code", "=", "outgoing"),
                    ("barcode", "=", "EOBR"),
                    ("company_id", "in", [company.id, False]),
                ], limit=1)
                or pt_model.search([
                    ("code", "=", "outgoing"),
                    ("sequence_code", "=", "EOBR"),
                    ("company_id", "in", [company.id, False]),
                ], limit=1)
            )

        return pt_obras_in, pt_eobr

    def _pg_obras_is_pg_obras_type(self):
        """True se for Obras:Receipts ou EOBR."""
        self.ensure_one()
        if not self.picking_type_id:
            return False
        pt_obras_in, pt_eobr = self._pg_obras_get_picking_types()
        return bool(
            (pt_obras_in and self.picking_type_id.id == pt_obras_in.id)
            or (pt_eobr and self.picking_type_id.id == pt_eobr.id)
        )

    def _pg_obras_should_set_analytic(self):
        """
        Regra contabilística:
        - Receipts: NUNCA meter analítica (evita duplicação)
        - EOBR: meter analítica
        """
        self.ensure_one()
        if not self.picking_type_id:
            return False
        _pt_obras_in, pt_eobr = self._pg_obras_get_picking_types()
        return bool(pt_eobr and self.picking_type_id.id == pt_eobr.id)

    def _pg_obras_build_project_vals(self):
        self.ensure_one()
        dist = self._pg_obras_get_project_distribution()
        dest = self._pg_obras_get_project_location()
        return dist, dest

    # ------------------------------------------------------------
    # Core: aplicar destino (sempre) + analítica (só se permitido)
    # ------------------------------------------------------------

    def _pg_obras_apply_to_moves_and_lines(self, dist, dest, set_analytic=False):
        """
        Garante que o destino REAL do stock (move + move lines) fica no projeto.
        NOTA: analítica só escreve se set_analytic=True.
        """
        for picking in self:
            # Moves
            for move in picking.move_ids_without_package:
                move_vals = {}
                if dest and move.location_dest_id != dest:
                    move_vals["location_dest_id"] = dest.id

                if set_analytic and "analytic_distribution" in move._fields:
                    if (move.analytic_distribution or {}) != (dist or {}):
                        move_vals["analytic_distribution"] = dist

                if move_vals:
                    move.with_context(pg_obras_skip_project_sync=True).write(move_vals)

                # Move lines
                for ml in move.move_line_ids:
                    ml_vals = {}
                    if dest and ml.location_dest_id != dest:
                        ml_vals["location_dest_id"] = dest.id

                    if set_analytic and "analytic_distribution" in ml._fields:
                        if (ml.analytic_distribution or {}) != (dist or {}):
                            ml_vals["analytic_distribution"] = dist

                    if ml_vals:
                        ml.with_context(pg_obras_skip_project_sync=True).write(ml_vals)

            # Também nas move lines “sem package”
            for ml in picking.move_line_ids_without_package:
                ml_vals = {}
                if dest and ml.location_dest_id != dest:
                    ml_vals["location_dest_id"] = dest.id

                if set_analytic and "analytic_distribution" in ml._fields:
                    if (ml.analytic_distribution or {}) != (dist or {}):
                        ml_vals["analytic_distribution"] = dist

                if ml_vals:
                    ml.with_context(pg_obras_skip_project_sync=True).write(ml_vals)

    # ------------------------------------------------------------
    # Sync logic (create/write/validate)
    # ------------------------------------------------------------

    def _pg_obras_sync_project_data(self):
        for picking in self:
            if picking.state in ("done", "cancel"):
                continue
            if not picking._pg_obras_is_pg_obras_type():
                continue
            if "project_id" not in picking._fields or not picking.project_id:
                continue

            dist, dest = picking._pg_obras_build_project_vals()
            set_analytic = picking._pg_obras_should_set_analytic()

            vals_picking = {}

            # Header destination
            if dest and picking.location_dest_id != dest:
                vals_picking["location_dest_id"] = dest.id

            # Header analytic (só se permitido)
            if set_analytic and "analytic_distribution" in picking._fields:
                if (picking.analytic_distribution or {}) != (dist or {}):
                    vals_picking["analytic_distribution"] = dist

            if vals_picking:
                picking.with_context(pg_obras_skip_project_sync=True).write(vals_picking)

            # ESSENCIAL: destino real no stock + analítica condicional
            picking._pg_obras_apply_to_moves_and_lines(dist, dest, set_analytic=set_analytic)

    # ------------------------------------------------------------
    # Onchange (sem writes!)
    # ------------------------------------------------------------

    def _pg_obras_onchange_project_data(self):
        for picking in self:
            if not picking._pg_obras_is_pg_obras_type():
                continue
            if "project_id" not in picking._fields or not picking.project_id:
                continue

            dist, dest = picking._pg_obras_build_project_vals()
            set_analytic = picking._pg_obras_should_set_analytic()

            # Header
            if dest:
                picking.location_dest_id = dest
            if set_analytic and "analytic_distribution" in picking._fields:
                picking.analytic_distribution = dist

            # Moves / lines (atribuição direta; sem writes)
            for move in picking.move_ids_without_package:
                if dest:
                    move.location_dest_id = dest
                if set_analytic and "analytic_distribution" in move._fields:
                    move.analytic_distribution = dist

                for ml in move.move_line_ids:
                    if dest:
                        ml.location_dest_id = dest
                    if set_analytic and "analytic_distribution" in ml._fields:
                        ml.analytic_distribution = dist

            for ml in picking.move_line_ids_without_package:
                if dest:
                    ml.location_dest_id = dest
                if set_analytic and "analytic_distribution" in ml._fields:
                    ml.analytic_distribution = dist

    # ------------------------------------------------------------
    # Hooks
    # ------------------------------------------------------------

    @api.onchange("project_id", "picking_type_id")
    def _onchange_pg_obras_project_data(self):
        self._pg_obras_onchange_project_data()

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get("pg_obras_skip_project_sync"):
            records._pg_obras_sync_project_data()
        return records

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get("pg_obras_skip_project_sync"):
            return res
        if any(k in vals for k in ("project_id", "picking_type_id")):
            self._pg_obras_sync_project_data()
        return res

    # ------------------------------------------------------------
    # Validate safeguard (muito importante!)
    # ------------------------------------------------------------

    def button_validate(self):
        """
        Antes de validar, garantir que moves + move lines têm o destino do projeto.
        Evita o caso: header certo, mas stock cai em OBR/Stock.
        """
        if not self.env.context.get("pg_obras_skip_project_sync"):
            self._pg_obras_sync_project_data()
        return super().button_validate()
