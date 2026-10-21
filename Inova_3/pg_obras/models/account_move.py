from odoo import _, api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    x_fechar_projeto = fields.Boolean(string="Fechar Projeto")

    def action_post(self):
        res = super().action_post()
        for move in self:
            move._handle_project_closure_pickings()
        return res

    def _get_related_project(self):
        """Find the project linked to the invoice or its analytic distribution.

        Priority:
        1) Explicit project_id on the invoice (if field exists).
        2) Explicit project_id on invoice lines (if field exists).
        3) Project from analytic accounts referenced in analytic_distribution on lines.
        """
        self.ensure_one()

        # 1) Campo direto no documento
        if "project_id" in self._fields and self.project_id:
            return self.project_id

        # 2) Campo direto nas linhas
        if "project_id" in self.invoice_line_ids._fields:
            for line in self.invoice_line_ids:
                if line.project_id:
                    return line.project_id

        # 3) Analytic distribution -> analytic account -> project
        if "analytic_distribution" in self.invoice_line_ids._fields:
            analytic_ids = set()
            for line in self.invoice_line_ids:
                dist = line.analytic_distribution or {}
                # keys podem ser strings
                for a_id in dist.keys():
                    try:
                        analytic_ids.add(int(a_id))
                    except Exception:
                        continue

            if analytic_ids:
                analytic_accounts = self.env["account.analytic.account"].browse(list(analytic_ids))
                for acc in analytic_accounts:
                    # project_ids pode ser recordset
                    if getattr(acc, "project_ids", False):
                        # se houver vários, pega no primeiro
                        return acc.project_ids[0]

        return False

    def _get_project_source_location(self, project, partner):
        if project and "x_localizacao_projeto" in project._fields and project.x_localizacao_projeto:
            return project.x_localizacao_projeto
        if partner and getattr(partner, "x_localizacao_obra", False):
            return partner.x_localizacao_obra
        return self.env["stock.location"]


    def _handle_project_closure_pickings(self):
        """Processo completo de fecho de projeto:
        1) Criar picking OUT da obra para o cliente.
        2) Validar picking automaticamente.
        3) Encontrar o movimento contabilístico gerado pelo OUT.
        4) Alterar a linha 321000 -> 361000.
        """
        self.ensure_one()

        # Apenas faturas de cliente com fecho ativado
        if self.move_type != "out_invoice" or not self.x_fechar_projeto:
            return

        partner = self.partner_id

        # 0) Identificar projeto ligado à fatura (ANTES de determinar localização)
        project_id = self._get_related_project()

        # 0.1) Determinar localização origem do fecho (prioridade: localização do projeto)
        obra_location = self._get_project_source_location(project_id, partner)
        if not obra_location or not obra_location.id:
            raise UserError(_("Não foi possível determinar a localização de origem da obra/projeto."))

        picking_type = self._get_outgoing_picking_type()

        customer_location = (
            picking_type.default_location_dest_id
            or partner.with_company(self.company_id).property_stock_customer
        )
        if not customer_location:
            raise UserError(_("Não foi possível determinar localização de destino."))

        # ------------------------------------------------------------
        # 1) Stock na Obra (origem = localização do projeto/obra)
        # ------------------------------------------------------------
        quants = self.env["stock.quant"].search([
            ("location_id", "=", obra_location.id),
            ("quantity", ">", 0),
            ("company_id", "=", self.company_id.id),
        ])

        if not quants:
            raise UserError(_("Não há stock disponível na localização da obra/projeto."))

        picking_move_type = (
            getattr(picking_type, "default_move_type", False)
            or getattr(picking_type, "move_type", "direct")
        )

        # Analítica do projeto (se existir)
        analytic_dist = {}
        if project_id and getattr(project_id, "account_id", False):
            analytic_dist = {project_id.account_id.id: 100}

        # ------------------------------------------------------------
        # 2) Criar Picking OUT (obra/projeto -> cliente)
        # ------------------------------------------------------------
        picking_vals = {
            "picking_type_id": picking_type.id,
            "location_id": obra_location.id,
            "location_dest_id": customer_location.id,
            "partner_id": partner.id,
            "company_id": self.company_id.id,
            "origin": self.name,
            "move_type": picking_move_type,
        }

        if project_id and "project_id" in self.env["stock.picking"]._fields:
            picking_vals["project_id"] = project_id.id

        picking = self.env["stock.picking"].with_context(default_move_type=False).create(picking_vals)

        moves = self.env["stock.move"]
        for quant in quants:
            move_vals = {
                "name": quant.product_id.display_name,
                "picking_id": picking.id,
                "product_id": quant.product_id.id,
                "product_uom_qty": quant.quantity,
                "product_uom": quant.product_uom_id.id,
                "location_id": obra_location.id,
                "location_dest_id": customer_location.id,
                "company_id": self.company_id.id,
            }
            if analytic_dist:
                move_vals["analytic_distribution"] = analytic_dist
            moves |= self.env["stock.move"].create(move_vals)

        # ------------------------------------------------------------
        # 3) Validar Picking
        # ------------------------------------------------------------
        picking.action_confirm()
        picking.action_assign()

        for move in moves:
            for move_line in move.move_line_ids:
                qty_to_do = move.product_uom_qty
                if move_line.product_uom_id != move.product_uom:
                    qty_to_do = move.product_uom._compute_quantity(
                        move.product_uom_qty, move_line.product_uom_id
                    )
                move_line.qty_done = qty_to_do

                # Reforço: analítica também na move line (quando existir o campo)
                if analytic_dist and "analytic_distribution" in move_line._fields:
                    move_line.analytic_distribution = analytic_dist

        picking.button_validate()

         # ------------------------------------------------------------
        # 4) Ajustar movimentos de valorização (321000 → 361000)
        #    Odoo v18: localizar via stock.valuation.layer (robusto)
        # ------------------------------------------------------------
        # 4) Ajustar movimentos de valorização (321000 → 361000)
        #    Odoo v18: localizar via stock.valuation.layer (robusto)
        # ------------------------------------------------------------
        conta_321 = self.env["account.account"].search([("code", "=", "321000")], limit=1)
        conta_361 = self.env["account.account"].search([("code", "=", "361000")], limit=1)

        if not conta_321 or not conta_361:
            raise UserError(_("Contas 321000 e/ou 361000 não existem para esta empresa."))

        categories = picking.move_ids.product_id.categ_id
        valuation_journals = categories.mapped("property_stock_journal").filtered(
            lambda j: j and (not j.company_id or j.company_id == self.company_id)
        )

        if not valuation_journals:
            raise UserError(_("Não foi encontrado Stock Journal (property_stock_journal) nas categorias dos produtos do picking."))
        if len(valuation_journals) > 1:
            raise UserError(_("Existem várias categorias com Stock Journal diferente. Defina um único diário para este fluxo de fecho."))
        expected_journal = valuation_journals[0]

        svls = self.env["stock.valuation.layer"].search([
            ("stock_move_id.picking_id", "=", picking.id),
            ("company_id", "=", self.company_id.id),
        ])
        moves_out = svls.mapped("account_move_id").filtered(lambda m: m)

        _logger.info(
            "[ProjectClose] Valuation lookup invoice=%s picking=%s svls=%s moves=%s expected_journal=%s",
            self.name, picking.name, len(svls), len(moves_out), expected_journal.display_name
        )

        if not moves_out:
            raise UserError(_("Nenhum movimento contabilístico de valorização foi gerado para o picking %s.") % picking.name)

        updated_any = False
        for move_out in moves_out:
            if move_out.journal_id != expected_journal:
                raise UserError(_(
                    "Movimento de valorização %s está no diário '%s', mas esperava '%s'."
                ) % (move_out.name, move_out.journal_id.display_name, expected_journal.display_name))

            linhas_321 = move_out.line_ids.filtered(lambda l: l.account_id.id == conta_321.id)
            if not linhas_321:
                continue

            was_posted = (move_out.state == "posted")
            if was_posted:
                move_out.button_draft()

            # Trocar 321 -> 361 e aplicar analítica
            linhas_321.write({
                "account_id": conta_361.id,
                "analytic_distribution": analytic_dist,
            })

            # Garantir analítica nas linhas 361
            move_out.line_ids.filtered(lambda l: l.account_id.id == conta_361.id).write({
                "analytic_distribution": analytic_dist,
            })

            _logger.info(
                "[ProjectClose] Reclass 321->361 invoice=%s picking=%s move=%s lines=%s analytic=%s",
                self.name, picking.name, move_out.name, len(linhas_321), bool(analytic_dist)
            )

            if was_posted:
                move_out.action_post()

            updated_any = True

        if not updated_any:
            raise UserError(_(
                "Foram encontrados movimentos de valorização para %s, mas nenhum tinha linhas em 321000 para reclassificar."
            ) % picking.name)

    def _get_outgoing_picking_type(self):
        self.ensure_one()
        company = self.company_id or self.env.company

        picking_type = self.env["stock.picking.type"].search([
            ("sequence_code", "=", "OUT"),
            ("warehouse_id.company_id", "=", company.id),
        ], limit=1)

        if not picking_type:
            picking_type = self.env["stock.picking.type"].search([("code", "=", "OUT")], limit=1)

        if not picking_type:
            raise UserError(_("Não foi possível encontrar o tipo de operação 'out'."))

        return picking_type

    