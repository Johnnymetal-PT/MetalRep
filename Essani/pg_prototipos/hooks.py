# -*- coding: utf-8 -*-
"""Migração dos campos criados à mão durante a fase de configuração.

Antes deste módulo existir, a ligação projeto↔artigo e a linhagem de versões eram
dois campos manuais (`x_pg_artigo_prototipo`, `x_pg_versao_origem`) criados por API.
Os valores que já lá estão têm de passar para os campos declarados pelo módulo,
senão os protótipos existentes perdem a ligação no dia da instalação.

Os campos antigos **não são apagados**: ficam como estavam, para que a operação
seja reversível. Desativam-se depois, com a migração confirmada.
"""

import logging

_logger = logging.getLogger(__name__)

CODIGO_SEQUENCIA = "pg.prototipo.ref"

PARES = [
    ("x_pg_artigo_prototipo", "pg_artigo_prototipo"),
    ("x_pg_versao_origem", "pg_versao_origem"),
]


def post_init_migrar_campos_manuais(env):
    projeto = env["project.project"]
    for antigo, novo in PARES:
        if antigo not in projeto._fields:
            _logger.info("pg_prototipos: %s não existe nesta base, nada a migrar.", antigo)
            continue
        # active_test=False: um protótipo arquivado continua a ser histórico útil e
        # perder-lhe a ligação seria uma perda silenciosa.
        registos = projeto.with_context(active_test=False).search(
            [(antigo, "!=", False), (novo, "=", False)])
        for registo in registos:
            registo[novo] = registo[antigo]
        _logger.info("pg_prototipos: %s -> %s, %d registos migrados.",
                     antigo, novo, len(registos))
    _consolidar_sequencia(env)


def _consolidar_sequencia(env):
    """Deixa uma única sequência `pg.prototipo.ref`, e no contador mais alto.

    Durante a fase de configuração a sequência foi criada por script, sem identificador
    externo. Ao instalar, o módulo cria a sua — e passam a existir duas com o mesmo
    código. O `next_by_code` escolheria uma delas, e as referências recomeçavam do
    princípio: PROT-2026-0001 seria atribuída duas vezes.

    Fica a do módulo, porque é a que as atualizações sabem gerir, mas herda o contador
    mais alto de todas — nunca se reutiliza um número que já saiu para um artigo. As
    outras são arquivadas, não apagadas.
    """
    sequencias = env["ir.sequence"].with_context(active_test=False).search(
        [("code", "=", CODIGO_SEQUENCIA)])
    if len(sequencias) < 2:
        return
    do_modulo = env.ref("pg_prototipos.seq_pg_prototipo_ref", raise_if_not_found=False)
    if not do_modulo:
        return
    maximo = max(sequencias.mapped("number_next_actual") or [1])
    do_modulo.write({"number_next": maximo, "active": True})
    outras = sequencias - do_modulo
    outras.write({"active": False})
    _logger.info(
        "pg_prototipos: %d sequências duplicadas arquivadas; contador fixado em %d.",
        len(outras), maximo)
