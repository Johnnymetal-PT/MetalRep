from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    has_orphan_landed_lines = fields.Boolean(
        compute='_compute_has_orphan_landed_lines',
        help='Verdadeiro se a factura tem linhas com produto landed_cost_ok=True '
             'sem ligação a purchase_line_id — candidatas a Ajuste de Importação.',
    )
    related_import_adjustment_ids = fields.One2many(
        'import.document.adjustment',
        'source_invoice_id',
        string='Ajustes de Importação Gerados',
        readonly=True,
    )
    import_adjustment_count = fields.Integer(
        compute='_compute_import_adjustment_count',
    )

    @api.depends('invoice_line_ids', 'invoice_line_ids.product_id', 'invoice_line_ids.purchase_line_id')
    def _compute_has_orphan_landed_lines(self):
        for move in self:
            move.has_orphan_landed_lines = bool(move._get_orphan_landed_lines())

    @api.depends('related_import_adjustment_ids')
    def _compute_import_adjustment_count(self):
        for move in self:
            move.import_adjustment_count = len(move.related_import_adjustment_ids)

    def _get_orphan_landed_lines(self):
        """Linhas da factura com produto landed_cost_ok=True E sem purchase_line_id.

        Estas são as linhas candidatas a Ajuste de Importação — representam um
        custo de aquisição (ex.: "Acerto Compras Custo") que o fornecedor cobrou
        mas não estava na PO original.
        """
        self.ensure_one()
        if self.move_type not in ('in_invoice', 'in_refund'):
            return self.env['account.move.line']
        return self.invoice_line_ids.filtered(
            lambda l: (
                l.display_type == 'product'
                and l.product_id
                and l.product_id.landed_cost_ok
                and not l.purchase_line_id
                and l.price_subtotal != 0
            )
        )

    def _find_related_import_document(self):
        """Procura o import.document associado a esta factura.

        Estratégia: das outras linhas DA MESMA factura que TÊM purchase_line_id,
        recolhe as POs e procura import.document que as inclua. Se houver
        ambiguidade (várias IMPs), retorna o primeiro mas regista warning.
        """
        self.ensure_one()
        lines_with_po = self.invoice_line_ids.filtered('purchase_line_id')
        if not lines_with_po:
            return self.env['import.document']

        po_ids = lines_with_po.mapped('purchase_line_id.order_id').ids
        if not po_ids:
            return self.env['import.document']

        imports = self.env['import.document'].search([
            ('purchase_order_ids', 'in', po_ids),
        ])
        if len(imports) > 1:
            _logger.warning(
                "Factura %s tem POs em múltiplos IMPs (%s) — usando o primeiro.",
                self.name, imports.mapped('name'),
            )
        return imports[:1]

    # ───────────────── Hook principal ─────────────────
    def _post(self, soft=True):
        """Override _post para criar ADJ em rascunho quando há linhas órfãs."""
        posted = super()._post(soft=soft)
        for move in posted.filtered(lambda m: m.move_type in ('in_invoice', 'in_refund')):
            try:
                move._create_import_adjustment_draft()
            except Exception as e:
                _logger.exception(
                    "Falha ao criar ADJ draft a partir de %s: %s", move.name, e,
                )
        return posted

    def _create_import_adjustment_draft(self):
        """Cria ImportDocumentAdjustment em rascunho se houver linhas órfãs."""
        self.ensure_one()
        orphan_lines = self._get_orphan_landed_lines()
        if not orphan_lines:
            return

        # Já existe ajuste para esta combinação? (constraint SQL trata isso, mas
        # evita disparar erro de constraint)
        existing = self.env['import.document.adjustment'].search([
            ('source_invoice_id', '=', self.id),
        ], limit=1)
        if existing:
            _logger.info(
                "Factura %s já tem ADJ %s — não duplicando.",
                self.name, existing.name,
            )
            return

        imp = self._find_related_import_document()
        if not imp:
            _logger.info(
                "Factura %s tem linhas com landed_cost_ok sem PO, mas não "
                "encontrei IMP associado — saltando criação de ADJ.",
                self.name,
            )
            return

        # balance = valor em moeda da empresa (já convertido ao câmbio da
        # factura). Evita subvalorizar quando a factura é em moeda estrangeira.
        total = sum(orphan_lines.mapped('balance'))
        adj = self.env['import.document.adjustment'].create({
            'import_id': imp.id,
            'source_invoice_id': self.id,
            'source_invoice_line_ids': [(6, 0, orphan_lines.ids)],
            'amount': total,
            'date': self.invoice_date or self.date or fields.Date.today(),
            'notes': _(
                "Gerado automaticamente ao postar a factura %(inv)s.\n"
                "Linhas detectadas: %(n)d (produto landed_cost_ok=True sem PO).\n"
                "Total: %(amount).2f %(curr)s\n"
                "IMP associado: %(imp)s"
            ) % {
                'inv': self.name,
                'n': len(orphan_lines),
                'amount': total,
                'curr': self.company_id.currency_id.name,
                'imp': imp.name,
            },
        })
        _logger.info("ADJ %s criado em rascunho a partir de %s para %s",
                     adj.name, self.name, imp.name)

        # Activity para o operador rever
        try:
            adj.activity_schedule(
                'mh_import_adjustment.mail_activity_review_adjustment',
                summary=_("Rever Ajuste de Importação"),
                note=_(
                    "Factura %(inv)s tem %(n)d linhas de custo sem PO "
                    "(total %(amount).2f). Revê e aplica o ajuste no IMP %(imp)s."
                ) % {
                    'inv': self.name,
                    'n': len(orphan_lines),
                    'amount': total,
                    'imp': imp.name,
                },
                user_id=self.invoice_user_id.id or self.env.user.id,
            )
        except ValueError:
            # activity_type pode ainda não estar carregado em primeira instalação
            _logger.warning("Activity type 'mail_activity_review_adjustment' não encontrado.")

    def action_view_import_adjustments(self):
        self.ensure_one()
        return {
            'name': _('Ajustes de Importação'),
            'type': 'ir.actions.act_window',
            'res_model': 'import.document.adjustment',
            'view_mode': 'list,form',
            'domain': [('source_invoice_id', '=', self.id)],
        }
