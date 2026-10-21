#!/usr/bin/env python3
"""Despublica uma página do website da Lusosofá, com resguardo e verificação.

Por defeito faz **dry-run**. Para escrever mesmo:

    python3 scripts_lusosofa/despublicar_pagina.py /our-services --aplicar

Despublicar não apaga nada: a página e a sua vista continuam na base, e
repõem-se com um `write` inverso — o comando exacto fica escrito no resguardo.
É a diferença entre desactivar e eliminar, e é sempre a desactivação que se
faz primeiro.

O que esta ferramenta recusa fazer:

* despublicar uma página que esteja num menu do site, ou que outra vista
  referencie — nesse caso haveria uma ligação a apontar para uma página que
  deixou de responder, e isso é pior do que o problema que se queria resolver.
  Com ``--mesmo-assim`` avança na mesma, depois de dizer o que encontrou.
"""

import argparse
import datetime
import json
import os
import pathlib
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aplicar_identidade import Odoo, RAIZ  # noqa: E402


def dependentes(odoo, url):
    menus = odoo.search_read("website.menu", [["url", "like", url]], ["name", "url"])
    vistas = odoo.kw("ir.ui.view", "search_read", [[["arch_db", "like", url]]],
                     {"fields": ["name", "key"], "limit": 20})
    return menus, vistas


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url", help="URL da página, por exemplo /our-services")
    ap.add_argument("--id", type=int, dest="pagina_id",
                    help="id da página, quando houver mais do que uma no mesmo URL. "
                         "Nomear o id É a desambiguação: a recusa existe para "
                         "impedir a escolha cega, não para impedir a escolha.")
    ap.add_argument("--aplicar", action="store_true", help="escreve mesmo")
    ap.add_argument("--mesmo-assim", action="store_true", dest="mesmo_assim",
                    help="avança mesmo havendo menus ou vistas a apontar para ela")
    ap.add_argument("--creds", default=os.path.expanduser("~/.lusosofa_odoo.json"))
    args = ap.parse_args()

    odoo = Odoo(json.load(open(args.creds, encoding="utf-8")))
    modo = "APLICAR" if args.aplicar else "dry-run (não escreve nada)"
    print(f"\nDespublicar {args.url} [{modo}]")
    print(f"{odoo.url} · base {odoo.db} · uid {odoo.uid}\n")

    pags = odoo.search_read("website.page", [["url", "=", args.url]],
                            ["id", "name", "url", "is_published", "website_indexed"])
    if not pags:
        raise SystemExit(f"ABORTADO: não existe página com o URL {args.url}")

    if args.pagina_id:
        escolhidas = [p for p in pags if p["id"] == args.pagina_id]
        if not escolhidas:
            raise SystemExit(f"ABORTADO: não há página id={args.pagina_id} em {args.url}. "
                             f"Existem: {[p['id'] for p in pags]}")
        pag = escolhidas[0]
        if len(pags) > 1:
            print(f"  atenção: {len(pags)} páginas em {args.url}; escolhida a "
                  f"id={pag['id']} por indicação expressa\n")
    elif len(pags) > 1:
        raise SystemExit(
            f"ABORTADO: há {len(pags)} páginas com esse URL e nenhuma foi indicada — "
            f"{[p['id'] for p in pags]}. Confirma qual é a servida e repete com "
            f"--id <id>. Escolher às cegas pode tirar do ar a página que o site usa."
        )
    else:
        pag = pags[0]
    print(f"  página: {pag['name']!r} (id {pag['id']})")
    print(f"  publicada={pag['is_published']}  indexada={pag['website_indexed']}")
    if not pag["is_published"]:
        print("\n  já está despublicada — nada a fazer.")
        return

    menus, vistas = dependentes(odoo, args.url)
    print(f"  menus a apontar-lhe: {[m['name'] for m in menus] or 'nenhum'}")
    print(f"  vistas que a citam:  {[v['key'] or v['name'] for v in vistas] or 'nenhuma'}")

    # As ligações apontam para o URL, não para o registo. Se outra página
    # publicada continuar a servir o mesmo URL, despublicar esta não deixa
    # ligação nenhuma pendurada — o endereço continua a responder.
    #
    # Sem esta distinção o travão dispara no caso mais comum de todos: tirar
    # do ar o duplicado que ninguém serve. Recusaria exactamente a limpeza que
    # existe para tornar segura.
    suplente = [p for p in pags if p["id"] != pag["id"] and p["is_published"]]
    if suplente:
        print(f"  outra página publicada serve {args.url}: id={suplente[0]['id']} "
              f"— o URL continua a responder")

    if (menus or vistas) and not suplente and not args.mesmo_assim:
        raise SystemExit(
            "\nABORTADO: despublicá-la deixaria ligações a apontar para uma página "
            "que deixa de responder. Retira-as primeiro, ou usa --mesmo-assim."
        )

    if not args.aplicar:
        print("\n  [dry-run] despublicaria e retiraria da indexação.")
        print("  Nada foi escrito. Para aplicar: --aplicar\n")
        return

    carimbo = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    destino = RAIZ / f".backup_lusosofa_pagina_{carimbo}.json"
    destino.write_text(json.dumps({
        "tirado_em_utc": carimbo,
        "base": odoo.db,
        "url": odoo.url,
        "accao": f"despublicar {args.url}",
        "estado_anterior": pag,
        "menus_que_apontavam": menus,
        "vistas_que_citavam": [v["key"] or v["name"] for v in vistas],
        "como_reverter": (
            f"website.page write [[{pag['id']}], "
            f"{{'is_published': True, 'website_indexed': True}}]"
        ),
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n  resguardo: {destino.name}")

    odoo.kw("website.page", "write",
            [[pag["id"]], {"is_published": False, "website_indexed": False}])

    # Verificar contra o destino, não contra o que a escrita disse.
    depois = odoo.search_read("website.page", [["id", "=", pag["id"]]],
                              ["is_published", "website_indexed"])[0]
    print(f"  na base: publicada={depois['is_published']} "
          f"indexada={depois['website_indexed']}")

    pedido = urllib.request.Request(odoo.url + args.url)
    try:
        with urllib.request.urlopen(pedido, timeout=60) as r:
            codigo = r.status
    except urllib.error.HTTPError as e:
        codigo = e.code
    print(f"  visitante anónimo em {args.url}: HTTP {codigo}")

    # O que se espera do URL depende de haver ou não quem o continue a servir.
    # Com suplente, um 200 é o resultado certo e não um sinal de falha — o que
    # se tirou do ar foi o registo duplicado, não o endereço.
    if suplente:
        ok = not depois["is_published"] and codigo == 200
        recado = ("Duplicado despublicado; o URL continua servido pela outra página."
                  if ok else "ATENÇÃO: o URL deixou de responder. Vê o resguardo.")
    else:
        ok = not depois["is_published"] and codigo != 200
        recado = ("Despublicada." if ok else
                  "ATENÇÃO: continua a responder a visitantes. Vê o resguardo.")
    print("\n" + recado)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
