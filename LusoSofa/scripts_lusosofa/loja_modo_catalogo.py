#!/usr/bin/env python3
"""Põe a loja a comportar-se como o catálogo que hoje é.

Por defeito faz **dry-run**. Para escrever mesmo:

    python3 scripts_lusosofa/loja_modo_catalogo.py --aplicar

Enquanto não houver preços, a loja mostrava debaixo de cada um dos 12 artigos:

    Not Available For Sale

Em inglês, numa loja em português, doze vezes. É o texto que o Odoo traz de
origem no campo ``prevent_zero_price_sale_text`` e que ninguém trocou. Ao lado,
o filtro «Gama de Preços» anunciava um intervalo de ``0,00 € — 0,00 €``.

Nada disto é defeito técnico: o site está a descrever com exactidão um catálogo
sem preços. O problema é o que a frase diz a quem chega — «não está à venda» é
uma recusa, e não é isso que a LusoSofá quer anunciar. «Sob consulta» diz o
mesmo facto e abre uma conversa.

O filtro de preços desaparece pela mesma razão: filtrar por um intervalo que
vai de zero a zero não ajuda ninguém e denuncia que os preços não existem.

**Quando os preços chegarem, isto inverte-se** — o texto deixa de aparecer
sozinho, porque o Odoo só o mostra enquanto o preço for zero, e o filtro
reactiva-se ligando a vista outra vez. Por isso se desactiva em vez de apagar.
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

TEXTO_ODOO = "Not Available For Sale"
TEXTO_PT = "Sob consulta"
TEXTO_ES = "Consultar precio"
VISTA_FILTRO = "website_sale.filter_products_price"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true", help="escreve mesmo")
    ap.add_argument("--creds", default=os.path.expanduser("~/.lusosofa_odoo.json"))
    args = ap.parse_args()

    odoo = Odoo(json.load(open(args.creds, encoding="utf-8")))
    modo = "APLICAR" if args.aplicar else "dry-run (não escreve nada)"
    print(f"\nLoja em modo catálogo [{modo}]")
    print(f"{odoo.url} · base {odoo.db}\n")

    site = odoo.search_read("website", [],
                            ["id", "prevent_zero_price_sale",
                             "prevent_zero_price_sale_text"])[0]
    print("1. texto em vez do preço")
    print(f"   esconder 'Adicionar ao carrinho' com preço zero: {site['prevent_zero_price_sale']}")
    print(f"   texto actual: {site['prevent_zero_price_sale_text']!r}")
    print(f"   -> {TEXTO_PT!r} (pt) · {TEXTO_ES!r} (es)")

    print("\n2. filtro de preços")
    filtro = odoo.kw("ir.ui.view", "search_read", [[["key", "=", VISTA_FILTRO]]],
                     {"fields": ["id", "active"], "context": {"active_test": False}})
    if not filtro:
        print(f"   ! não encontrei {VISTA_FILTRO}")
    else:
        print(f"   {VISTA_FILTRO}: "
              f"{'activo — seria desactivado' if filtro[0]['active'] else 'já desactivado'}")

    # Quantos artigos estão de facto a zero. Se algum já tiver preço, a
    # decisão muda — não se esconde um estado que já não é geral.
    zero = odoo.search_read("product.template",
                            [["is_published", "=", True], ["list_price", "=", 0]], ["name"])
    todos = odoo.search_read("product.template", [["is_published", "=", True]], ["id"])
    print(f"\n3. artigos publicados a 0,00: {len(zero)} de {len(todos)}")
    if zero and len(zero) != len(todos):
        print("   ! já há artigos com preço — confirma se ainda faz sentido esconder")

    if not args.aplicar:
        print("\n  Nada foi escrito. Para aplicar: --aplicar\n")
        return

    carimbo = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    destino = RAIZ / f".backup_lusosofa_catalogo_{carimbo}.json"
    destino.write_text(json.dumps({
        "tirado_em_utc": carimbo, "base": odoo.db, "url": odoo.url,
        "accao": "loja em modo catálogo enquanto não há preços",
        "website_antes": site, "filtro_antes": filtro,
        "como_reverter": (f"repor prevent_zero_price_sale_text e reactivar {VISTA_FILTRO}"),
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n  resguardo: {destino.name}")

    # A origem primeiro, a tradução depois e por update_field_translations:
    # escrever a tradução com `lang` no contexto substituiria a origem, como
    # aconteceu nas descrições dos artigos a 2026-09-28.
    odoo.kw("website", "write", [[site["id"]], {"prevent_zero_price_sale_text": TEXTO_PT}],
            {"context": {"lang": "en_US"}})
    odoo.kw("website", "update_field_translations",
            [[site["id"]], "prevent_zero_price_sale_text", {"es_ES": TEXTO_ES}])
    print(f"  texto: {TEXTO_PT!r} / {TEXTO_ES!r}")

    if filtro and filtro[0]["active"]:
        odoo.kw("ir.ui.view", "write", [[filtro[0]["id"]], {"active": False}])
        print(f"  {VISTA_FILTRO} desactivado")

    print("\nverificação — contra a loja servida, nas duas línguas")
    ok = True
    for caminho, quer, nao_quer in [("/shop", TEXTO_PT, TEXTO_ODOO),
                                    ("/es/shop", TEXTO_ES, TEXTO_ODOO)]:
        h = urllib.request.urlopen(odoo.url + caminho, timeout=90).read().decode("utf-8", "replace")
        n = len(re.findall(re.escape(quer), h))
        limpo = nao_quer not in h
        sem_filtro = "Gama de Preços" not in h and "Rango de Precios" not in h
        print(f"  {caminho:10} {quer!r}: {n}x   sem {nao_quer!r}: "
              f"{'sim' if limpo else 'NÃO'}   sem filtro de preços: {'sim' if sem_filtro else 'NÃO'}")
        ok = ok and n >= 10 and limpo and sem_filtro

    print("\n" + ("Loja em modo catálogo." if ok else
                  "ATENÇÃO: algo não confere. Vê o resguardo."))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
