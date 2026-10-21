#!/usr/bin/env python3
"""Tira as ligações sem destino dos quatro modelos na homepage.

Por defeito faz **dry-run**. Para escrever mesmo:

    python3 scripts_lusosofa/corrigir_ligacoes_modelos.py --aplicar

Encontrado a 2026-09-26, na varredura de todas as ligações internas do site.
A secção «A Nossa Seleção» da homepage nomeia quatro modelos da Coleção
Traços — Noa, Porto, Estoril e Alcântara — e cada nome é uma ligação para uma
página que nunca existiu. Quatro 404 na primeira página do site. A do
Alcântara tinha ainda o endereço trocado (``/alcanatara``).

**Porque se removem em vez de se repontarem.** Os quatro modelos não estão no
catálogo: a loja tem outras doze peças, nenhuma delas Noa, Porto, Estoril ou
Alcântara. Mandar quem clica para ``/shop`` seria prometer uma coisa e mostrar
outra — pior do que não haver ligação. Os nomes ficam como texto, que é o que
sempre foram na prática.

Fica por decidir, e é decisão do cliente: se estes quatro modelos merecem
página própria, ou se devem entrar no catálogo.
"""

import argparse
import datetime
import json
import os
import re
import sys
import urllib.request
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aplicar_identidade import Odoo, RAIZ  # noqa: E402

MODELOS = ["noa", "porto", "estoril", "alcanatara"]

# As fotografias dos quatro cartões estão dentro de âncoras sem destino
# (``href="#"``): clicar não faz nada. É defeito diferente do de cima — aquele
# era nos nomes, este é no próprio cartão — e foi encontrado a 2026-09-26, ao
# olhar para a secção com outra pergunta em mente.
#
# Tira-se a âncora e deixa-se a fotografia. Apontá-la a algum lado exigiria
# saber para onde, e os quatro modelos não têm página nem estão no catálogo.
#
# O alvo é preciso de propósito — só as âncoras com este `aria-label` — para
# não apanhar controlos de carrossel e outros `href="#"` que o Odoo usa
# legitimamente noutros sítios da mesma página.
ANCORA_MORTA = re.compile(
    r'<a[^>]*aria-label="Link to product"[^>]*href="#"[^>]*>(.*?)</a>', re.S)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true", help="escreve mesmo")
    ap.add_argument("--creds", default=os.path.expanduser("~/.lusosofa_odoo.json"))
    args = ap.parse_args()

    odoo = Odoo(json.load(open(args.creds, encoding="utf-8")))
    modo = "APLICAR" if args.aplicar else "dry-run (não escreve nada)"
    print(f"\nLigações dos modelos na homepage [{modo}]")
    print(f"{odoo.url} · base {odoo.db}\n")

    pag = [p for p in odoo.search_read("website.page", [["url", "=", "/"]],
                                       ["id", "view_id", "is_published"]) if p["is_published"]]
    if len(pag) != 1:
        raise SystemExit(f"ABORTADO: esperava uma homepage publicada, encontrei {len(pag)}.")
    vid = pag[0]["view_id"][0]
    antes = odoo.kw("ir.ui.view", "read", [[vid], ["arch_db"]],
                    {"context": {"lang": "en_US"}})[0]["arch_db"]

    depois = antes
    total = 0
    for slug in MODELOS:
        padrao = re.compile(r'<a[^>]+href="/%s"[^>]*>(.*?)</a>' % re.escape(slug), re.S)
        for m in padrao.finditer(depois):
            print(f"   /{slug:11} -> texto {m.group(1).strip()!r}")
            total += 1
        depois = padrao.sub(lambda m: m.group(1), depois)
    if not total:
        print("   nenhuma ligação de modelo encontrada  (já corrigido?)")

    n_ancoras = len(ANCORA_MORTA.findall(depois))
    print(f"\n   âncoras sem destino nos cartões: {n_ancoras}")
    depois = ANCORA_MORTA.sub(lambda m: m.group(1), depois)
    total += n_ancoras

    def levantar():
        por_lingua = {}
        for t in odoo.kw("ir.ui.view", "get_field_translations", [[vid], "arch_db"])[0]:
            v = t.get("value")
            if not v:
                continue
            novo = v
            for slug in MODELOS:
                novo = re.sub(r'<a[^>]+href="/%s"[^>]*>(.*?)</a>' % re.escape(slug),
                              lambda m: m.group(1), novo, flags=re.S)
            novo = ANCORA_MORTA.sub(lambda m: m.group(1), novo)
            if novo != v:
                por_lingua.setdefault(t["lang"], {})[t["source"]] = novo
        return por_lingua

    print("\n  valores traduzidos com a mesma ligação:")
    pendentes = levantar()
    for lang, m in pendentes.items():
        print(f"   {lang}: {len(m)} valor(es)")
    if not pendentes:
        print("   nenhum")

    mudou = depois != antes
    if not mudou and not pendentes:
        print("\n  Nada a mudar.\n")
        return
    if mudou:
        try:
            xml.dom.minidom.parseString(depois)
        except Exception as e:
            raise SystemExit(f"ABORTADO: o resultado não é XML válido — {e}")
        print(f"\n  vista: {len(antes)} -> {len(depois)} caracteres, XML válido")

    if not args.aplicar:
        print("\n  Nada foi escrito. Para aplicar: --aplicar\n")
        return

    carimbo = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    destino = RAIZ / f".backup_lusosofa_modelos_{carimbo}.json"
    destino.write_text(json.dumps({
        "tirado_em_utc": carimbo, "base": odoo.db, "url": odoo.url,
        "accao": "remover ligações sem destino dos modelos na homepage",
        "vista": vid, "arch_db_antes": antes,
        "como_reverter": f"ir.ui.view write [[{vid}], {{'arch_db': <arch_db_antes>}}] com lang en_US",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n  resguardo: {destino.name}")

    if mudou:
        odoo.kw("ir.ui.view", "write", [[vid], {"arch_db": depois}],
                {"context": {"lang": "en_US"}})
        print(f"  origem escrita — {total} ligação(ões) removida(s)")
    for lang, mapa in levantar().items():
        odoo.kw("ir.ui.view", "update_field_translations", [[vid], "arch_db", {lang: mapa}])
        print(f"  {lang}: {len(mapa)} valor(es) traduzido(s) corrigidos")

    print("\nverificação — contra as páginas servidas")
    ok = True
    for caminho in ["/", "/es"]:
        h = urllib.request.urlopen(odoo.url + caminho, timeout=90).read().decode("utf-8", "replace")
        restam = [s for s in MODELOS if f'href="/{s}"' in h or f'href="{caminho}/{s}"' in h]
        mortas = len(ANCORA_MORTA.findall(h))
        print(f"  {caminho:5} ligações de modelo: {restam or 'nenhuma'}   "
              f"âncoras sem destino: {mortas}")
        ok = ok and not restam and mortas == 0
        # As fotografias e os nomes têm de ficar: o que se tira é a ligação,
        # não o conteúdo.
        for nome in ["Modelo Noa", "Modelo Porto", "Modelo Estoril", "Modelo Alcântara"]:
            if nome not in h:
                print(f"  ! {caminho} perdeu o texto {nome!r}")
                ok = False
        imagens = len(re.findall(r'<img[^>]+o_card_img', h))
        print(f"        fotografias dos cartões: {imagens}")
        ok = ok and imagens >= 4

    print("\n" + ("Ligações removidas, nomes mantidos." if ok else
                  "ATENÇÃO: algo não confere. Vê o resguardo."))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
