# -*- coding: utf-8 -*-
"""Coloca os manuais internos no topo da árvore e dá-lhes acesso a todos os internos.

Duas alterações, ambas no **artigo de raiz** (os filhos seguem-no):

  1. `sequence` → passa a ser o primeiro entre os artigos de raiz.
     O `create` do Knowledge coloca cada artigo em último entre os irmãos salvo
     sequência explícita (`knowledge_article.py`, docstring do `create`), e foi por
     isso que a raiz nasceu no fim. Usa-se um valor **abaixo do mínimo actual** em
     vez de renumerar os outros: mexer em 19 artigos de produção para mudar a
     posição de um seria risco sem retorno.

  2. `is_article_visible_by_everyone` → True, e `internal_permission` → 'write'.
     Para um utilizador interno, o Knowledge mostra o artigo se este campo for True
     **ou** se o utilizador for membro (`_compute_is_article_visible`). Sem ele,
     ficava a depender de memberships pessoais. Os filhos herdam por compute
     recursivo a partir da raiz (`_compute_is_article_visible_by_everyone`), pelo
     que não é preciso — nem correcto — escrevê-lo em cada um.

Uso
---
    python pg_ajustar_acesso_knowledge.py                      # dry-run
    python pg_ajustar_acesso_knowledge.py --confirm --allow-prod

Idempotente: relê o estado e só escreve o que está diferente.
"""

from __future__ import annotations

import argparse
import os
import sys

PROJECT_KEY = "odoo-gbn"
PURPOSE = "production"
MODELO = "knowledge.article"
TITULO_RAIZ = "Manuais internos — GBN Travel"


def _raiz_do_repo(inicio: str) -> str:
    atual = os.path.abspath(inicio)
    while True:
        if os.path.exists(os.path.join(atual, ".pg_framework")):
            return atual
        pai = os.path.dirname(atual)
        if pai == atual:
            raise SystemExit("Não foi encontrada a raiz do repositório (pasta com '.pg_framework').")
        atual = pai


RAIZ = _raiz_do_repo(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, ".pg_framework", "scripts"))

from pg_odoo_migration_guard import (  # noqa: E402
    ErroDeGuarda,
    Guard,
    resolver_alvo_por_projeto,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--confirm", action="store_true")
    ap.add_argument("--allow-prod", action="store_true")
    ap.add_argument("--log", default=None)
    args = ap.parse_args()

    alvo = resolver_alvo_por_projeto(PROJECT_KEY, PURPOSE)
    print(f"Alvo : {alvo.base_url}  base='{alvo.database}'  finalidade='{alvo.purpose}'")
    print(f"Modo : {'ESCRITA' if args.confirm else 'DRY-RUN (nada é escrito)'}\n")

    guarda = Guard(alvo, confirmed=args.confirm, allow_prod=args.allow_prod, log_path=args.log)

    # -- estado actual --------------------------------------------------- #
    raizes = guarda.kw(MODELO, "search_read", [[["parent_id", "=", False]]],
                       {"fields": ["id", "name", "sequence",
                                   "is_article_visible_by_everyone", "internal_permission"]})
    nossa = next((r for r in raizes if r["name"] == TITULO_RAIZ), None)
    if not nossa:
        print(f"Artigo de raiz {TITULO_RAIZ!r} não encontrado. Correr primeiro "
              "pg_criar_artigos_knowledge.py.")
        return 1

    sequencia_minima = min(r["sequence"] for r in raizes)
    nova_sequencia = sequencia_minima - 1

    print(f"Raiz            : [{nossa['id']}] {nossa['name']}")
    print(f"sequence        : {nossa['sequence']}  ->  {nova_sequencia}  "
          f"(mínimo actual entre {len(raizes)} raízes: {sequencia_minima})")
    print(f"visível a todos : {nossa['is_article_visible_by_everyone']}  ->  True")
    print(f"permissão int.  : {nossa['internal_permission']!r}  ->  'write'")

    vals = {}
    if nossa["sequence"] != nova_sequencia:
        vals["sequence"] = nova_sequencia
    if not nossa["is_article_visible_by_everyone"]:
        vals["is_article_visible_by_everyone"] = True
    if nossa["internal_permission"] != "write":
        vals["internal_permission"] = "write"

    if not vals:
        print("\nNada a alterar: já está no estado pretendido.")
        return 0

    if not args.confirm:
        print(f"\nEscreveria em [{nossa['id']}]: {vals}")
        print("Dry-run terminado. Nada foi escrito.")
        print("Para executar: --confirm --allow-prod (a base é produção).")
        return 0

    guarda.kw(MODELO, "write", [[nossa["id"]], vals], allow_write=True)
    print(f"\nEscrito em [{nossa['id']}]: {vals}")

    # -- reconciliação ---------------------------------------------------- #
    print("\n--- Reconciliação ---")
    depois = guarda.kw(MODELO, "search_read",
                       [[["id", "child_of", nossa["id"]]]],
                       {"fields": ["id", "name", "sequence",
                                   "is_article_visible_by_everyone", "internal_permission"]})
    # A raiz é a primeira? Comparar contra as restantes raízes, relidas.
    raizes_depois = guarda.kw(MODELO, "search_read", [[["parent_id", "=", False]]],
                              {"fields": ["id", "sequence"]})
    primeira = min(raizes_depois, key=lambda r: (r["sequence"], r["id"]))
    invisiveis = [a["id"] for a in depois if not a["is_article_visible_by_everyone"]]

    print(f"Artigos na árvore        : {len(depois)}")
    print(f"Primeira raiz por sequence: [{primeira['id']}] "
          f"(esperado [{nossa['id']}])")
    print(f"Sem visibilidade herdada : {invisiveis or 'nenhum'}")

    if primeira["id"] != nossa["id"] or invisiveis:
        print("FALHA: o estado final não corresponde ao pretendido.")
        return 1
    print("OK: primeiro na árvore e visível a todos os utilizadores internos.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ErroDeGuarda as erro:
        print(f"\nGUARD: {erro}", file=sys.stderr)
        raise SystemExit(2)
