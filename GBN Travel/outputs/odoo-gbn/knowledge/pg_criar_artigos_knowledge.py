# -*- coding: utf-8 -*-
"""Cria/actualiza os tutoriais de Knowledge do projeto Odoo - GBN (tarefa 6737).

Toda a comunicação com o Odoo do cliente passa pelo `pg_odoo_migration_guard.py`,
conforme a regra obrigatória do `AGENTS_SHARED.md`. Este script não fala com o
Odoo directamente e não conhece credenciais: o alvo é resolvido a partir de
`pg.odoo.connection`, pelo canal Brodoo, em memória.

Uso
---
    # 1) dry-run (não escreve nada) — é sempre o primeiro passo
    python pg_criar_artigos_knowledge.py

    # 2) escrita, depois de o dry-run ter sido revisto
    #    a base da GBN é produção ('main' no nome), logo exige --allow-prod
    python pg_criar_artigos_knowledge.py --confirm --allow-prod

Idempotência
------------
Um artigo é reconhecido pelo par (título, artigo-pai). Se já existir, é
**actualizado**; se não, é criado. Correr o script duas vezes não duplica nada.
Nada é apagado nem arquivado — a regra da framework é não destruir camadas
anteriores.

Reconciliação
-------------
No fim, o script compara o que era esperado com o que existe no Odoo e imprime o
resultado. Uma execução sem reconciliação não está terminada.
"""

from __future__ import annotations

import argparse
import os
import sys

PROJECT_KEY = "odoo-gbn"
PURPOSE = "production"
MODELO = "knowledge.article"


def _raiz_do_repo(inicio: str) -> str:
    """Sobe até encontrar a pasta com o atalho `.pg_framework`."""
    atual = os.path.abspath(inicio)
    while True:
        if os.path.exists(os.path.join(atual, ".pg_framework")):
            return atual
        pai = os.path.dirname(atual)
        if pai == atual:
            raise SystemExit(
                "Não foi encontrada a raiz do repositório (pasta com '.pg_framework'). "
                "Correr o script de dentro do repositório do projeto."
            )
        atual = pai


RAIZ = _raiz_do_repo(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, ".pg_framework", "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pg_odoo_migration_guard import (  # noqa: E402
    ErroDeGuarda,
    Guard,
    resolver_alvo_por_projeto,
)
from artigos_conteudo import ARTIGOS  # noqa: E402


def validar_arvore(artigos: list[dict]) -> None:
    """Falha cedo em incoerências da árvore, antes de tocar no Odoo."""
    chaves = set()
    for a in artigos:
        if a["chave"] in chaves:
            raise SystemExit(f"Chave repetida na árvore: {a['chave']!r}")
        chaves.add(a["chave"])
    for a in artigos:
        pai = a.get("pai")
        if pai and pai not in chaves:
            raise SystemExit(f"Artigo {a['chave']!r} aponta para um pai inexistente: {pai!r}")
    # Os pais têm de vir antes dos filhos: o id do pai é preciso para criar o filho.
    vistos: set[str] = set()
    for a in artigos:
        if a.get("pai") and a["pai"] not in vistos:
            raise SystemExit(
                f"Ordem inválida: {a['chave']!r} aparece antes do seu pai {a['pai']!r}."
            )
        vistos.add(a["chave"])


def procurar_existente(guarda: Guard, titulo: str, pai_id: int | None) -> int | None:
    """id do artigo com este título sob este pai, ou None."""
    dominio = [["name", "=", titulo]]
    dominio.append(["parent_id", "=", pai_id] if pai_id else ["parent_id", "=", False])
    # `active_test: False` para reencontrar um artigo que tenha ido para o lixo:
    # sem isto criava-se um duplicado ao lado do que já existe, arquivado.
    ids = guarda.kw(MODELO, "search", [dominio], {"limit": 1, "context": {"active_test": False}})
    return ids[0] if ids else None


def valores_do_artigo(artigo: dict, pai_id: int | None) -> dict:
    vals = {
        "name": artigo["titulo"],
        "body": artigo["corpo"].strip(),
        "icon": artigo.get("icone") or False,
    }
    if pai_id:
        vals["parent_id"] = pai_id
    else:
        # Artigo de raiz: sem permissão interna definida ficaria fora do Workspace,
        # e o material é para ser visto por toda a equipa interna.
        vals["internal_permission"] = "write"
    return vals


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--confirm", action="store_true",
                    help="executar de facto; sem isto é dry-run")
    ap.add_argument("--allow-prod", action="store_true",
                    help="autorizar escrita em produção (exigido pelo guard)")
    ap.add_argument("--log", default=None, help="caminho do log de chamadas")
    args = ap.parse_args()

    validar_arvore(ARTIGOS)

    alvo = resolver_alvo_por_projeto(PROJECT_KEY, PURPOSE)
    print(f"Alvo   : {alvo.base_url}  base='{alvo.database}'  finalidade='{alvo.purpose}'")
    print(f"Modo   : {'ESCRITA' if args.confirm else 'DRY-RUN (nada é escrito)'}")
    print(f"Artigos: {len(ARTIGOS)}\n")

    guarda = Guard(alvo, confirmed=args.confirm, allow_prod=args.allow_prod,
                   log_path=args.log)

    # Profundidade de cada chave, só para o output refletir a árvore: é este texto
    # que se lê para autorizar uma escrita em produção, e um plano que não mostra a
    # hierarquia esconde exactamente o que há para validar.
    pais = {a["chave"]: a.get("pai") for a in ARTIGOS}

    def profundidade(chave: str) -> int:
        n, atual = 0, pais.get(chave)
        while atual:
            n, atual = n + 1, pais.get(atual)
        return n

    ids_por_chave: dict[str, int | None] = {}
    criados, actualizados, por_criar, por_actualizar = 0, 0, 0, 0

    for artigo in ARTIGOS:
        pai_id = ids_por_chave.get(artigo["pai"]) if artigo.get("pai") else None
        if artigo.get("pai") and pai_id is None and args.confirm:
            # Só é erro em escrita: em dry-run o pai pode ainda não existir.
            print(f"  ! {artigo['titulo']}: pai não resolvido, ignorado")
            ids_por_chave[artigo["chave"]] = None
            continue

        existente = procurar_existente(guarda, artigo["titulo"], pai_id)
        vals = valores_do_artigo(artigo, pai_id)
        nivel = profundidade(artigo["chave"])
        prefixo = "  " + ("    " * nivel) + ("└─ " if nivel else "")

        if existente:
            if args.confirm:
                guarda.kw(MODELO, "write", [[existente], vals], allow_write=True)
                actualizados += 1
                print(f"{prefixo}actualizado  [{existente}] {artigo['titulo']}")
            else:
                por_actualizar += 1
                print(f"{prefixo}actualizaria  [{existente}] {artigo['titulo']}")
            ids_por_chave[artigo["chave"]] = existente
        else:
            if args.confirm:
                novo = guarda.kw(MODELO, "create", [vals], allow_write=True)
                criados += 1
                print(f"{prefixo}criado       [{novo}] {artigo['titulo']}")
                ids_por_chave[artigo["chave"]] = novo
            else:
                por_criar += 1
                print(f"{prefixo}criaria       {artigo['titulo']}  "
                      f"({len(vals['body'])} caracteres de corpo)")
                ids_por_chave[artigo["chave"]] = None

    # -- reconciliação ------------------------------------------------- #
    print("\n--- Reconciliação ---")
    if args.confirm:
        print(f"Esperados : {len(ARTIGOS)}")
        print(f"Criados   : {criados}")
        print(f"Actualizados: {actualizados}")
        resolvidos = sum(1 for v in ids_por_chave.values() if v)
        print(f"No Odoo   : {resolvidos}")
        if resolvidos != len(ARTIGOS):
            print("FALHA: o número de artigos no Odoo não corresponde ao esperado.")
            return 1
        print("OK: origem e destino coincidem.")
    else:
        print(f"Esperados     : {len(ARTIGOS)}")
        print(f"Seriam criados: {por_criar}")
        print(f"Seriam actualizados: {por_actualizar}")
        print("\nDry-run terminado. Nada foi escrito.")
        print("Para executar: --confirm --allow-prod (a base é produção).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ErroDeGuarda as erro:
        print(f"\nGUARD: {erro}", file=sys.stderr)
        raise SystemExit(2)
