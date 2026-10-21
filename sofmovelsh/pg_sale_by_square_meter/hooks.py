import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Reporta as linhas herdadas cuja quantidade não corresponde à área.

    Deliberadamente **não corrige**. Na base migrada há linhas com fatura
    lançada; reescrever-lhes a quantidade mexeria em documentos contabilísticos
    já emitidos. A lista fica no log para ser tratada caso a caso.
    """
    divergentes = env['sale.order.line']._pg_report_area_mismatch()
    if divergentes:
        _logger.warning(
            "pg_sale_by_square_meter: %s linha(s) herdada(s) por rever. "
            "Não foram alteradas — ver o log acima.",
            len(divergentes),
        )
