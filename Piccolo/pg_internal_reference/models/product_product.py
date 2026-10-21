"""Atribuicao automatica de ``default_code`` a variantes de produto.

Sempre que uma ``product.product`` e criada sem ``default_code``,
deduz-se o prefixo a partir da primeira variante codificada do mesmo
template e gera-se ``<base>-<counter:05d>``.

Modelo herdado: ``product.product`` (override de ``create``).
"""
from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def create(self, vals):
        """Override create para gerar ``default_code`` quando esta vazio.

        O bloco esta dentro de try/except propositadamente: se a deducao
        do codigo falhar (ex.: template sem nenhuma variante codificada
        ainda), nao queremos abortar a criacao da variante - apenas
        deixa-la sem codigo e logar o erro.
        """
        product = super(ProductProduct, self).create(vals)

        try:
            if not product.default_code:
                # 1) Procurar a primeira variante deste template com codigo,
                #    para usar a parte antes do primeiro '-' como prefixo.
                first_variant = self.search([
                    ('product_tmpl_id', '=', product.product_tmpl_id.id),
                    ('default_code', '!=', False)
                ], limit=1, order="id asc")

                if first_variant:
                    base_code = first_variant.default_code.split('-')[0]

                    # 2) Listar codigos ja usados nesse template para calcular
                    #    o proximo contador.
                    existing_codes = self.search([
                        ('product_tmpl_id', '=', product.product_tmpl_id.id),
                        ('default_code', 'like', f"{base_code}-%")
                    ]).mapped('default_code')

                    # Aceita apenas sufixos numericos; ignora codigos manuais
                    # que nao sigam o padrao "BASE-N".
                    counters = [
                        int(code.split('-')[-1]) for code in existing_codes
                        if code.split('-')[-1].isdigit()
                    ]

                    next_counter = max(counters, default=0) + 1

                    # Formato fixo de 5 digitos para manter ordenacao
                    # alfabetica == ordenacao numerica.
                    product.default_code = f"{base_code}-{next_counter:05d}"
                    _logger.info(
                        "Assigned default_code %s to variant %s",
                        product.default_code, product.id,
                    )
                else:
                    _logger.warning(
                        "No base default_code found for product template %s. "
                        "Skipping default_code assignment.",
                        product.product_tmpl_id.id,
                    )

            # Backfill de eventuais variantes irmas sem codigo - util quando
            # se cria um lote de variantes onde so a primeira teve codigo.
            product.product_tmpl_id.product_variant_ids.assign_default_codes_to_all_variants()
        except Exception as e:
            # Nao re-raise: falhar a deducao do codigo nao deve bloquear
            # a criacao da variante. Erro fica registado para diagnostico.
            _logger.error("Error assigning default_code to product %s: %s", product.id, e)

        return product

    def assign_default_codes_to_all_variants(self):
        """Atribuir ``default_code`` a todas as variantes em falta.

        Util como reprocessamento manual para templates onde algumas
        variantes foram criadas antes de o modulo estar instalado.
        """
        for template in self.mapped('product_tmpl_id'):
            # Primeira variante codificada serve de fonte para o prefixo.
            first_variant = template.product_variant_ids.filtered(lambda v: v.default_code).sorted('id')
            if first_variant:
                base_code = first_variant[0].default_code.split('-')[0]

                # Calcular proximo contador a partir dos codigos existentes.
                existing_codes = template.product_variant_ids.mapped('default_code')
                counters = [
                    int(code.split('-')[-1]) for code in existing_codes
                    if code and code.split('-')[-1].isdigit()
                ]
                next_counter = max(counters, default=0) + 1

                for variant in template.product_variant_ids:
                    if not variant.default_code:
                        variant.default_code = f"{base_code}-{next_counter:05d}"
                        _logger.info(
                            "Assigned default_code %s to variant %s",
                            variant.default_code, variant.id,
                        )
                        next_counter += 1
            else:
                _logger.warning(
                    "No base default_code found for product template %s. "
                    "Skipping assignment for variants.",
                    template.id,
                )
