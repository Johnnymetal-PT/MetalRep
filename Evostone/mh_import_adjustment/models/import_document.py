from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ImportDocument(models.Model):
    _inherit = 'import.document'

    adjustment_ids = fields.One2many(
        'import.document.adjustment',
        'import_id',
        string='Ajustes Pós-Factura',
        readonly=True,
    )
    adjustment_count = fields.Integer(
        string='Nº Ajustes',
        compute='_compute_adjustment_count',
    )
    total_adjustments = fields.Monetary(
        string='Total Ajustes',
        compute='_compute_total_adjustments',
        currency_field='currency_id',
        help='Soma dos ajustes aplicados (state=applied)',
    )
    final_import_cost = fields.Monetary(
        string='Custo Final (c/ Ajustes)',
        compute='_compute_total_adjustments',
        currency_field='currency_id',
        help='total_import_cost + total_adjustments. Não persistido — '
             'reflecte o valor real após todos os ajustes aplicados.',
    )

    @api.depends('adjustment_ids')
    def _compute_adjustment_count(self):
        for doc in self:
            doc.adjustment_count = len(doc.adjustment_ids)

    @api.depends('adjustment_ids.state', 'adjustment_ids.amount', 'total_import_cost')
    def _compute_total_adjustments(self):
        for doc in self:
            applied = doc.adjustment_ids.filtered(lambda a: a.state == 'applied')
            doc.total_adjustments = sum(applied.mapped('amount'))
            doc.final_import_cost = doc.total_import_cost + doc.total_adjustments

    def action_view_adjustments(self):
        self.ensure_one()
        return {
            'name': 'Ajustes Pós-Factura',
            'type': 'ir.actions.act_window',
            'res_model': 'import.document.adjustment',
            'view_mode': 'list,form',
            'domain': [('import_id', '=', self.id)],
            'context': {'default_import_id': self.id},
        }

    # ───────────────── Validação de configuração PCMP ─────────────────
    def _get_landed_products(self):
        """Produtos físicos dos pickings do IMP — alvo do LC + accounting."""
        self.ensure_one()
        moves = self.picking_ids.move_ids
        return moves.mapped('product_id').filtered(
            lambda p: p.type == 'consu' or p.is_storable
        )

    def _check_products_configuration(self):
        """Bloqueia avanço se algum produto físico do IMP estiver mal configurado
        para o fluxo PCMP + Landed Cost.

        Ordem de verificação (acumula TODOS os erros antes de levantar):
          1. categoria.property_valuation == 'real_time'
             (PCMP exige contabilização contínua — manual_periodic deixa o
             account.move sem linhas para o produto, causando divergência
             entre SVL pool e contabilidade)
          2. categoria tem stock_output e stock_valuation accounts definidos
             (necessário para o ajuste CMV do ADJ funcionar)
        """
        self.ensure_one()
        non_real_time = []
        missing_accounts = []

        for product in self._get_landed_products():
            categ = product.categ_id
            if categ.property_valuation != 'real_time':
                non_real_time.append((product, categ))
                continue  # se nem é real_time, contas não importam

            accounts = product.product_tmpl_id.get_product_accounts()
            problems = []
            if not accounts.get('stock_output'):
                problems.append('stock_output')
            if not accounts.get('stock_valuation'):
                problems.append('stock_valuation')
            if problems:
                missing_accounts.append((product, problems))

        if non_real_time:
            lines = '\n'.join(
                "  • %s — categoria '%s' (property_valuation=%s)" % (
                    p.display_name, c.name, c.property_valuation)
                for p, c in non_real_time
            )
            raise UserError(_(
                "Não é possível avançar — produtos cuja categoria tem "
                "'Inventory Valuation' diferente de 'Automated':\n\n%(lines)s\n\n"
                "Configure a categoria com property_valuation='real_time' "
                "antes de finalizar o IMP. Caso contrário, o account.move do "
                "Landed Cost ficará sem linhas para esses produtos, divergindo "
                "do pool de valorização."
            ) % {'lines': lines})

        if missing_accounts:
            lines = '\n'.join(
                "  • %s — categoria '%s' sem: %s" % (
                    p.display_name, p.categ_id.name, ', '.join(missing))
                for p, missing in missing_accounts
            )
            raise UserError(_(
                "Não é possível avançar — produtos sem contas de stock "
                "configuradas:\n\n%(lines)s\n\n"
                "Configure 'Stock Output Account' e 'Stock Valuation Account' "
                "nas categorias destes produtos."
            ) % {'lines': lines})

    # ───────────────── Override das acções de finalização ─────────────────
    def action_finalize_provisional(self):
        for doc in self:
            doc._check_products_configuration()
        return super().action_finalize_provisional()

    def action_receive_with_costs(self):
        for doc in self:
            doc._check_products_configuration()
        return super().action_receive_with_costs()
