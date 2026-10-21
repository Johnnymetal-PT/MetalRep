#!/usr/bin/env python3
"""Arruma o cabeçalho, o menu e a grafia dos nomes do catálogo.

Por defeito faz **dry-run**. Para escrever mesmo:

    python3 scripts_lusosofa/arrumar_cabecalho_e_menu.py --aplicar

Quatro alterações decididas a 2026-09-28, depois de olhar para o site montado:

**1. As fichas de projeto saem do cabeçalho para o rodapé.** Em itálico
minúsculo ao lado da lupa pareciam erro. São a publicidade obrigatória de
projetos cofinanciados e o sítio delas é o rodapé, onde esse tipo de menção
vive em qualquer site.

**2. A lupa sai.** Com doze artigos, uma caixa de pesquisa não encontra nada
que a loja não mostre na primeira página.

**3. O «Iniciar Sessão» sai.** Ninguém cria conta numa loja que ainda não
vende, e o botão ocupava o canto mais valioso do cabeçalho.

**4. «Projetos» entra no menu.** A página existe e o rodapé leva lá; o menu
não. Uma página fora do menu é uma página que ninguém encontra.

E, à parte, os nomes do catálogo passam de maiúsculas a caixa normal:
«CADEIRÃO EMILY GIRATÓRIO» grita, e a tipografia nova não pede isso.

**Todas as desactivações são de vistas de opção**, que é o que o painel de
personalização do editor faz quando se desliga um elemento do cabeçalho. Não
se apaga nada: repõe-se ligando outra vez.
"""

import argparse
import datetime
import json
import os
import re
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aplicar_identidade import Odoo, RAIZ  # noqa: E402

# chave -> porquê
DESLIGAR = {
    "website.header_text_element": "fichas de projeto em itálico minúsculo",
    "website.header_search_box": "pesquisa desnecessária com 12 artigos",
}

MENU_NOVO = {"name": "Projetos", "url": "/projetos", "sequence": 3}
ARVORE = "Top Menu for Website 1"

# As fichas vão para a coluna da marca no rodapé.
VISTA_RODAPE = "website.template_footer_links"
PROJETOS_RODAPE = (
    '<p class="text-muted"><span style="font-size: .8rem;">'
    '<a href="/web/content/778?download=true" target="_blank">'
    '<font class="text-o-color-3">Projeto 70484</font></a>'
    '&amp;nbsp;&amp;nbsp;·&amp;nbsp;&amp;nbsp;'
    '<a href="/web/content/783?download=true" target="_blank">'
    '<font class="text-o-color-3">Projeto 71172</font></a>'
    '</span></p>'
)
ANCORA_RODAPE = ('<span style="font-size: 1.125rem;">'
                 '<font class="text-o-color-3">Porto - Portugal</font></span></p>')

PAGINAS = ["/", "/shop", "/about-us", "/projetos", "/contactus",
           "/es", "/es/shop", "/es/projetos", "/web/login", "/my"]


def estado(odoo):
    fora = {}
    for u in PAGINAS:
        try:
            fora[u] = urllib.request.urlopen(odoo.url + u, timeout=45).status
        except urllib.error.HTTPError as e:
            fora[u] = e.code
        except Exception as e:
            fora[u] = type(e).__name__
    return fora


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true", help="escreve mesmo")
    ap.add_argument("--creds", default=os.path.expanduser("~/.lusosofa_odoo.json"))
    args = ap.parse_args()

    odoo = Odoo(json.load(open(args.creds, encoding="utf-8")))
    modo = "APLICAR" if args.aplicar else "dry-run (não escreve nada)"
    print(f"\nCabeçalho, menu e catálogo [{modo}]")
    print(f"{odoo.url} · base {odoo.db}\n")

    print("1. vistas de opção a desligar")
    alvos = []
    for chave, porque in DESLIGAR.items():
        vs = odoo.kw("ir.ui.view", "search_read", [[["key", "=", chave], ["active", "=", True]]],
                     {"fields": ["id", "website_id"], "context": {"active_test": False}})
        for v in vs:
            alvos.append(v["id"])
            print(f"   {chave:36} id={v['id']:5} — {porque}")
        if not vs:
            print(f"   {chave:36} já desligada")

    print("\n2. menu")
    arv = odoo.search_read("website.menu", [["name", "=", ARVORE]], ["id"])
    if not arv:
        raise SystemExit(f"ABORTADO: não encontrei a árvore {ARVORE!r}.")
    ja = odoo.search_read("website.menu",
                          [["parent_id", "=", arv[0]["id"]], ["url", "=", MENU_NOVO["url"]]], ["id"])
    print(f"   «{MENU_NOVO['name']}» -> {MENU_NOVO['url']}: "
          f"{'já existe' if ja else 'seria criado, sequência ' + str(MENU_NOVO['sequence'])}")

    print("\n3. nomes do catálogo")
    produtos = odoo.search_read("product.template", [["is_published", "=", True]], ["id", "name"])
    renomear = []
    for p in produtos:
        novo = " ".join(w.capitalize() if w.isupper() else w for w in p["name"].split())
        if novo != p["name"]:
            renomear.append((p["id"], p["name"], novo))
    for _, velho, novo in renomear[:4]:
        print(f"   {velho:32} -> {novo}")
    print(f"   ({len(renomear)} de {len(produtos)} artigos)")

    print("\n4. fichas de projeto para o rodapé")
    rod = odoo.kw("ir.ui.view", "search_read",
                  [[["key", "=", VISTA_RODAPE], ["website_id", "!=", False]]],
                  {"fields": ["id"], "context": {"active_test": False}})[0]
    arch_rod = odoo.kw("ir.ui.view", "read", [[rod["id"]], ["arch_db"]],
                       {"context": {"lang": "en_US"}})[0]["arch_db"]
    tem = "web/content/778" in arch_rod
    print(f"   rodapé já tem as fichas: {'sim' if tem else 'não'}")
    if not tem and arch_rod.count(ANCORA_RODAPE) != 1:
        raise SystemExit("ABORTADO: não encontrei onde inserir as fichas no rodapé.")

    if not args.aplicar:
        print("\n  Nada foi escrito. Para aplicar: --aplicar\n")
        return

    antes_estado = estado(odoo)
    carimbo = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    destino = RAIZ / f".backup_lusosofa_cabecalho_{carimbo}.json"
    destino.write_text(json.dumps({
        "tirado_em_utc": carimbo, "base": odoo.db, "url": odoo.url,
        "accao": "arrumar cabeçalho, menu e nomes do catálogo",
        "vistas_desligadas": alvos, "rodape_id": rod["id"], "rodape_arch_antes": arch_rod,
        "nomes_antes": [{"id": i, "name": v} for i, v, _ in renomear],
        "estado_antes": antes_estado,
        "como_reverter": "reactivar as vistas, repor o arch do rodapé e os nomes",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n  resguardo: {destino.name}")

    if not tem:
        novo_rod = arch_rod.replace(ANCORA_RODAPE, ANCORA_RODAPE + PROJETOS_RODAPE, 1)
        odoo.kw("ir.ui.view", "write", [[rod["id"]], {"arch_db": novo_rod}],
                {"context": {"lang": "en_US"}})
        print("  fichas de projeto acrescentadas ao rodapé")

    for vid in alvos:
        odoo.kw("ir.ui.view", "write", [[vid], {"active": False}])
    print(f"  {len(alvos)} vistas de opção desligadas")

    if not ja:
        odoo.kw("website.menu", "create", [{
            "name": MENU_NOVO["name"], "url": MENU_NOVO["url"],
            "parent_id": arv[0]["id"], "sequence": MENU_NOVO["sequence"],
            "website_id": odoo.search_read("website", [], ["id"])[0]["id"],
        }])
        odoo.kw("website.menu", "write",
                [[m["id"] for m in odoo.search_read(
                    "website.menu", [["parent_id", "=", arv[0]["id"]],
                                     ["url", "=", "/contactus"]], ["id"])], {"sequence": 4}])
        print("  menu «Projetos» criado")

    for pid, velho, novo in renomear:
        odoo.kw("product.template", "write", [[pid], {"name": novo}],
                {"context": {"lang": "en_US"}})
        # A mesma armadilha das descrições: a tradução tapa a origem.
        for t in odoo.kw("product.template", "get_field_translations", [[pid], "name"])[0]:
            if t.get("value") and t["value"] != novo:
                odoo.kw("product.template", "update_field_translations",
                        [[pid], "name", {t["lang"]: novo}])
    print(f"  {len(renomear)} nomes de artigo em caixa normal")

    print("\nverificação — nenhuma página pode mudar de comportamento")
    ok = True
    depois = estado(odoo)
    for u, c in depois.items():
        if c != antes_estado[u]:
            print(f"  ! {u}: {antes_estado[u]} -> {c}")
            ok = False
    print(f"  as {len(PAGINAS)} páginas respondem como antes: {'sim' if ok else 'NÃO'}")
    if not ok:
        for vid in alvos:
            odoo.kw("ir.ui.view", "write", [[vid], {"active": True}])
        print("  REVERTIDO: as vistas de opção voltaram a activas")
        sys.exit(1)

    h = urllib.request.urlopen(odoo.url + "/", timeout=90).read().decode("utf-8", "replace")
    rodape = re.search(r"<footer.*?</footer>", h, re.S)
    corpo_rod = rodape.group(0) if rodape else ""
    cabeca = h[:h.find("</header>")] if "</header>" in h else h

    for o_que, presente, onde in [
        ("Iniciar Sessão no cabeçalho", "Iniciar Sessão" in cabeca, False),
        ("caixa de pesquisa no cabeçalho", "o_searchbar" in cabeca or "search" in cabeca.lower(), False),
        ("Projeto 70484 no cabeçalho", "Projeto 70484" in cabeca, False),
        ("Projeto 70484 no rodapé", "Projeto 70484" in corpo_rod, True),
        ("«Projetos» no menu", ">Projetos<" in cabeca, True),
    ]:
        marca = "  " if presente == onde else "! "
        print(f"{marca}{o_que}: {'sim' if presente else 'não'}")
        ok = ok and presente == onde

    nomes = [p["name"] for p in odoo.search_read("product.template",
                                                 [["is_published", "=", True]], ["name"])]
    gritam = [n for n in nomes if n == n.upper() and any(c.isalpha() for c in n)]
    print(f"  nomes ainda todos em maiúsculas: {gritam or 'nenhum'}")
    ok = ok and not gritam

    print("\n" + ("Cabeçalho e catálogo arrumados." if ok else
                  "ATENÇÃO: algo não confere. Vê o resguardo."))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
