import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    pg_template_code = fields.Char(
        string="Referência do Artigo",
        copy=False,
        index='btree_not_null',
        help="Referência ao nível do artigo, independente das variantes.\n"
             "Na V17 este valor vivia no campo standard 'Referência Interna' do"
             " artigo. Em v19 esse campo passa a ser derivado das variantes e é"
             " reposto a vazio em artigos com mais do que uma variante, pelo que"
             " a referência do artigo precisa de campo próprio.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        templates = super().create(vals_list)
        for template in templates:
            if not template.pg_template_code:
                template.pg_template_code = self.env['product.product']._pg_next_sequence_number()
        return templates

    # ------------------------------------------------------------------
    # Acções
    # ------------------------------------------------------------------

    def action_pg_generate_references(self):
        """Gera o que estiver em falta nos artigos seleccionados.

        Substitui o uso manual da server action 973 da V17 ("PG Gerar Código
        Barras").
        """
        variants = self.mapped('product_variant_ids')
        for template in self:
            if not template.pg_template_code:
                template.pg_template_code = self.env['product.product']._pg_next_sequence_number()

        updated = variants._pg_fill_missing() if variants else 0

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': _("%(templates)s artigo(s) e %(variants)s variante(s) actualizados.",
                             templates=len(self), variants=updated),
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

    # ------------------------------------------------------------------
    # Recuperação de dados existentes
    # ------------------------------------------------------------------

    @api.model
    def _pg_snapshot_template_codes(self):
        """Guarda em `pg_template_code` a referência que o artigo tem hoje.

        Tem de correr **antes** de qualquer escrita de `default_code` nas
        variantes. Na base migrada da V17, artigos com várias variantes têm um
        `default_code` gravado que o standard v19 considera derivado das
        variantes: à primeira escrita numa variante esse valor é recalculado e
        fica vazio. Este método copia-o para campo próprio primeiro.

        Idempotente: só escreve onde `pg_template_code` ainda está vazio.

        :return: número de artigos actualizados
        """
        templates = self.with_context(active_test=False).search([
            ('default_code', '!=', False),
            ('pg_template_code', '=', False),
        ])
        for template in templates:
            template.pg_template_code = template.default_code

        _logger.info(
            "pg_product_reference: referência de artigo preservada em %s registo(s).",
            len(templates),
        )
        return len(templates)
