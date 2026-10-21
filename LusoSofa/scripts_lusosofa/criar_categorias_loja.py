#!/usr/bin/env python3
"""Cria as categorias da loja da Lusosofá e arruma os artigos nelas.

Por defeito faz **dry-run**. Para escrever mesmo:

    python3 scripts_lusosofa/criar_categorias_loja.py --aplicar

Estrutura escolhida (opção B, decidida a 2026-09-24): três categorias em vez
das cinco que o catálogo sugere à letra. Com doze artigos, «Camas» tinha uma
peça lá dentro e «Chaise longues» duas — menus que se abrem para quase nada.
As três agrupam por onde a peça vive em casa, e cada uma tem volume.

É idempotente: encontra pelo nome as categorias que já existam, cria as que
faltem, e reescreve a arrumação dos artigos. Correr duas vezes dá o mesmo
resultado que correr uma.

A classificação é por regra, não por lista de nomes escritos à mão, para que um
artigo novo no catálogo caia sozinho no sítio certo. Em troca, o script
**recusa-se a escrever** se algum artigo não encaixar em nenhuma regra ou
encaixar em duas: prefere parar a arrumar mal em silêncio.
"""

import argparse
import datetime
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aplicar_identidade import Odoo, RAIZ  # noqa: E402


# nome, sequência, marcas que identificam o artigo pelo seu nome
ESTRUTURA = [
    ("Sofás e chaise longues", 10, ("SOFÁ", "MODULAR", "CHAISELONG")),
    ("Cadeirões",              20, ("CADEIRÃO",)),
    ("Quarto",                 30, ("CABECEIRA", "CAMA ")),
]


def classificar(produtos):
    """Devolve {categoria: [artigos]} e levanta erro se algum ficar por arrumar."""
    mapa = {nome: [] for nome, _, _ in ESTRUTURA}
    ambiguos, orfaos = [], []
    for p in produtos:
        coube = [nome for nome, _, marcas in ESTRUTURA
                 if any(m in p["name"] for m in marcas)]
        if len(coube) > 1:
            ambiguos.append((p["name"], coube))
        elif not coube:
            orfaos.append(p["name"])
        else:
            mapa[coube[0]].append(p)

    if orfaos or ambiguos:
        if orfaos:
            print(f"\n  ! sem categoria: {orfaos}")
        if ambiguos:
            print(f"\n  ! em mais do que uma: {ambiguos}")
        raise SystemExit(
            "ABORTADO: nem todos os artigos encaixam numa e numa só categoria. "
            "Ajusta as marcas em ESTRUTURA antes de escrever."
        )
    return mapa


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true", help="escreve mesmo")
    ap.add_argument("--creds", default=os.path.expanduser("~/.lusosofa_odoo.json"))
    args = ap.parse_args()

    odoo = Odoo(json.load(open(args.creds, encoding="utf-8")))
    modo = "APLICAR" if args.aplicar else "dry-run (não escreve nada)"
    print(f"\nCategorias da loja Lusosofá [{modo}]")
    print(f"{odoo.url} · base {odoo.db} · língua {odoo.lingua_do_site()}\n")

    produtos = odoo.search_read("product.template", [["is_published", "=", True]],
                                ["id", "name", "public_categ_ids"])
    print(f"  artigos publicados: {len(produtos)}")
    mapa = classificar(produtos)
    for nome, _, _ in ESTRUTURA:
        print(f"\n  {nome} ({len(mapa[nome])})")
        for p in sorted(mapa[nome], key=lambda r: r["name"]):
            print(f"     {p['name'].title()}")

    if not args.aplicar:
        print("\n  Nada foi escrito. Para aplicar: --aplicar\n")
        return

    carimbo = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    destino = RAIZ / f".backup_lusosofa_categorias_{carimbo}.json"
    destino.write_text(json.dumps({
        "tirado_em_utc": carimbo,
        "base": odoo.db,
        "url": odoo.url,
        "accao": "criar categorias da loja (opção B) e arrumar os artigos",
        "categorias_antes": odoo.search_read("product.public.category", [],
                                             ["name", "sequence"]),
        "artigos_antes": [{"id": p["id"], "name": p["name"],
                           "public_categ_ids": p["public_categ_ids"]} for p in produtos],
        "como_reverter": ("repor public_categ_ids de cada artigo com os valores acima "
                          "e apagar as categorias criadas (nenhum artigo tinha categoria)"),
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n  resguardo: {destino.name}")

    ids = {}
    for nome, seq, _ in ESTRUTURA:
        ja = odoo.search_read("product.public.category", [["name", "=", nome]], ["id"])
        if ja:
            ids[nome] = ja[0]["id"]
            odoo.kw("product.public.category", "write", [[ids[nome]], {"sequence": seq}])
            print(f"  já existia: {nome} (id {ids[nome]})")
        else:
            ids[nome] = odoo.kw("product.public.category", "create",
                                [{"name": nome, "sequence": seq}])
            print(f"  criada: {nome} (id {ids[nome]})")

    for nome, _, _ in ESTRUTURA:
        alvos = [p["id"] for p in mapa[nome]]
        if alvos:
            odoo.kw("product.template", "write",
                    [alvos, {"public_categ_ids": [(6, 0, [ids[nome]])]}])
            print(f"  arrumados {len(alvos)} artigos em {nome}")

    print("\nverificação")
    ok = True
    for p in odoo.search_read("product.template", [["is_published", "=", True]],
                              ["name", "public_categ_ids"]):
        if len(p["public_categ_ids"]) != 1:
            print(f"  ! {p['name']}: {len(p['public_categ_ids'])} categorias")
            ok = False
    if ok:
        print(f"  os {len(produtos)} artigos têm uma categoria cada")

    # A loja tem de as mostrar mesmo. A opção `products_categories_top` está
    # activa nesta base, mas isso é configuração — o que conta é a página.
    pagina = urllib.request.urlopen(odoo.url + "/shop", timeout=90).read().decode("utf-8", "replace")
    for nome, _, _ in ESTRUTURA:
        visivel = nome in re.sub(r"\s+", " ", pagina)
        print(f"  /shop mostra {nome!r}: {'sim' if visivel else 'NÃO'}")
        ok = ok and visivel

    print("\n" + ("Categorias criadas e visíveis." if ok else
                  "ATENÇÃO: alguma coisa não confere. Vê o resguardo."))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
