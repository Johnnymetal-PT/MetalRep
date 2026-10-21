import logging

_logger = logging.getLogger(__name__)

# Campo do módulo PG_Etiquetas_A5 da V17. Vive no mesmo modelo e tem os mesmos
# valores; muda só o nome.
CAMPO_ANTIGO = 'print_label_type'


def post_init_hook(env):
    """Recupera o tipo de etiqueta escolhido na V17.

    O campo passou a chamar-se `pg_label_type`. O nome antigo é mantido em vez de
    reaproveitado de propósito: com o mesmo nome, desinstalar o módulo da V17
    apagaria a coluna e levaria os dados — 8164 artigos em ZPL, 870 em 5x8 e 575 em
    A5 na produção. Assim os dois campos coexistem, copia-se um para o outro, e o
    módulo antigo pode ser desinstalado sem perder nada.

    Numa base v19 limpa o campo antigo não existe e não há nada a copiar.
    """
    Template = env['product.template']
    if CAMPO_ANTIGO not in Template._fields:
        _logger.info(
            "pg_etiquetas: campo '%s' não existe nesta base; nada a recuperar.",
            CAMPO_ANTIGO,
        )
        return

    # Só onde o campo novo ainda está por preencher: correr o hook uma segunda vez
    # não pode sobrepor escolhas já feitas em v19.
    artigos = Template.search([
        (CAMPO_ANTIGO, '!=', False),
        ('pg_label_type', '=', False),
    ])
    for tipo in ('A5', '5x8', 'ZPL'):
        lote = artigos.filtered(lambda a, t=tipo: a[CAMPO_ANTIGO] == t)
        if lote:
            lote.write({'pg_label_type': tipo})
            _logger.info(
                "pg_etiquetas: %s artigos recuperados para o tipo '%s'.", len(lote), tipo,
            )
