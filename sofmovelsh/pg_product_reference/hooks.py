import logging

from .models.product_product import SEQUENCE_CODE

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Prepara a base para a geração de referências.

    1. Cria a sequência `product.cod_artigo` **apenas se não existir**. Na base
       migrada da V17 ela já existe (com o contador no valor real) e não pode
       ser duplicada: `next_by_code` resolve por código e uma segunda sequência
       com o mesmo código faria recomeçar a numeração.
    2. Preserva em `pg_template_code` a referência que cada artigo tem hoje,
       antes de qualquer escrita nas variantes a poder apagar.
    """
    sequence = env['ir.sequence'].search([('code', '=', SEQUENCE_CODE)], limit=1)
    if sequence:
        _logger.info(
            "pg_product_reference: sequência '%s' já existe (id=%s, próximo=%s); mantida.",
            SEQUENCE_CODE, sequence.id, sequence.number_next_actual,
        )
    else:
        sequence = env['ir.sequence'].create({
            'name': "Product Code Sequence",
            'code': SEQUENCE_CODE,
            'padding': 7,
            'number_increment': 1,
            'implementation': 'standard',
            'company_id': False,
        })
        _logger.info(
            "pg_product_reference: sequência '%s' criada (id=%s).", SEQUENCE_CODE, sequence.id,
        )

    env['product.template']._pg_snapshot_template_codes()
