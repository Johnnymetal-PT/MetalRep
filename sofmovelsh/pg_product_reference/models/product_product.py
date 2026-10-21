import logging

from odoo import _, api, models
from odoo.exceptions import UserError
from odoo.tools.barcode import get_barcode_check_digit

_logger = logging.getLogger(__name__)

SEQUENCE_CODE = 'product.cod_artigo'

PARAM_EAN_PREFIX = 'pg_product_reference.ean_prefix'
PARAM_BARCODE_MODE = 'pg_product_reference.barcode_mode'
PARAM_MIRROR_STUDIO = 'pg_product_reference.mirror_studio'

DEFAULT_EAN_PREFIX = '843384'
DEFAULT_BARCODE_MODE = 'legacy'

# Espelho para os campos Studio herdados da V17, mantido durante a transicao.
# Chave = campo canonico Odoo; valor = campo Studio equivalente.
STUDIO_MIRROR_FIELDS = {
    'default_code': 'x_studio_referncia_interna',
    'barcode': 'x_studio_cdigo_de_barras',
}


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._pg_assign_reference_vals(vals)
        products = super().create(vals_list)
        products._pg_mirror_to_studio_fields()
        return products

    # ------------------------------------------------------------------
    # Geração
    # ------------------------------------------------------------------

    @api.model
    def _pg_assign_reference_vals(self, vals):
        """Preenche `default_code` e `barcode` em falta, a partir da sequência.

        Aplicado nos `vals` antes do `create`, para não haver uma segunda
        escrita. O contexto `pg_skip_auto_reference` desliga a geração (útil em
        importações que trazem os códigos de origem, e nos testes).
        """
        if self.env.context.get('pg_skip_auto_reference'):
            return

        if not vals.get('default_code'):
            number = self._pg_next_sequence_number()
            vals['default_code'] = number
            if not vals.get('barcode'):
                vals['barcode'] = self._pg_build_barcode(number)
        elif not vals.get('barcode'):
            # A referência veio de fora (código legado ou do fornecedor) mas
            # falta o código de barras. Consome-se um número só para o barcode,
            # pelo que aqui referência e barcode não coincidem — ao contrário
            # do caso em que ambos são gerados.
            vals['barcode'] = self._pg_build_barcode(self._pg_next_sequence_number())

    @api.model
    def _pg_next_sequence_number(self):
        number = self.env['ir.sequence'].next_by_code(SEQUENCE_CODE)
        if not number:
            raise UserError(_(
                "A sequência '%s' não existe ou não está configurada. Sem ela não é"
                " possível gerar a referência interna do produto.",
                SEQUENCE_CODE,
            ))
        return number

    @api.model
    def _pg_build_barcode(self, number):
        """Constrói o código de barras a partir do número de sequência.

        Dois modos, controlados pelo parâmetro de sistema
        `pg_product_reference.barcode_mode`:

        - `legacy` (por omissão): reproduz exactamente o formato da V17 —
          prefixo + número com 7 dígitos. Dá 13 caracteres, mas o último dígito
          é o da sequência e **não** o dígito de controlo EAN-13, pelo que a
          maioria dos códigos não é EAN-13 válido. Mantém-se por omissão porque
          é o formato das etiquetas já impressas e dos códigos já em base.
        - `ean13`: prefixo + número truncado a 12 dígitos + dígito de controlo
          calculado. Gera EAN-13 válido, mas passa a conviver com o formato
          antigo já existente.
        """
        params = self.env['ir.config_parameter'].sudo()
        prefix = params.get_param(PARAM_EAN_PREFIX, DEFAULT_EAN_PREFIX)
        mode = params.get_param(PARAM_BARCODE_MODE, DEFAULT_BARCODE_MODE)

        if mode == 'ean13':
            body = f"{prefix}{number}"[:12].ljust(12, '0')
            return f"{body}{get_barcode_check_digit(body + '0')}"

        return f"{prefix}{number.zfill(7)}"

    # ------------------------------------------------------------------
    # Espelho dos campos Studio
    # ------------------------------------------------------------------

    def _pg_mirror_to_studio_fields(self):
        """Copia referência e código de barras para os campos Studio da V17.

        Os campos `x_studio_*` só existem depois de a base migrada ser
        restaurada; num Odoo v19 limpo não existem e o espelho é ignorado.
        Escreve apenas quando o campo Studio está vazio — nunca sobrepõe um
        valor histórico.
        """
        if self.env['ir.config_parameter'].sudo().get_param(PARAM_MIRROR_STUDIO, 'True') == 'False':
            return

        mirror = {
            source: target
            for source, target in STUDIO_MIRROR_FIELDS.items()
            if target in self._fields
        }
        if not mirror:
            return

        for product in self:
            updates = {
                target: product[source]
                for source, target in mirror.items()
                if product[source] and not product[target]
            }
            if updates:
                product.write(updates)

    # ------------------------------------------------------------------
    # Recuperação de dados existentes
    # ------------------------------------------------------------------

    @api.model
    def _pg_backfill_references(self, limit=None):
        """Atribui referência e código de barras às variantes que não os têm.

        ATENÇÃO: escrever `default_code` numa variante dispara o recálculo de
        `product.template.default_code`. Em templates com mais do que uma
        variante o standard repõe esse campo a vazio — ver
        `product_template.py`, campo `pg_template_code`, e correr
        `_pg_snapshot_template_codes()` **antes** deste método.

        :param limit: processar no máximo N variantes (o método é idempotente,
            por isso pode ser chamado em lotes sucessivos até devolver 0)
        :return: número de variantes actualizadas
        """
        products = self.with_context(active_test=False).search(
            ['|', ('default_code', '=', False), ('barcode', '=', False)],
            limit=limit,
        )
        return products._pg_fill_missing()

    def _pg_fill_missing(self):
        """Preenche referência e código de barras em falta nas variantes de `self`.

        Usa a referência Studio herdada da V17 quando ela existe (não gasta
        número novo nem muda a referência que o cliente já conhece); só recorre
        à sequência quando não há nada para reaproveitar.

        :return: número de variantes actualizadas
        """
        has_studio_ref = STUDIO_MIRROR_FIELDS['default_code'] in self._fields
        has_studio_barcode = STUDIO_MIRROR_FIELDS['barcode'] in self._fields

        updated = 0
        for product in self:
            updates = {}

            if not product.default_code:
                inherited = has_studio_ref and product[STUDIO_MIRROR_FIELDS['default_code']]
                updates['default_code'] = inherited or self._pg_next_sequence_number()

            if not product.barcode:
                inherited = has_studio_barcode and product[STUDIO_MIRROR_FIELDS['barcode']]
                if inherited:
                    updates['barcode'] = inherited
                else:
                    source = updates.get('default_code') or product.default_code
                    updates['barcode'] = self._pg_build_barcode(source)

            if updates:
                product.write(updates)
                updated += 1

        _logger.info("pg_product_reference: %s variante(s) actualizada(s).", updated)
        return updated
