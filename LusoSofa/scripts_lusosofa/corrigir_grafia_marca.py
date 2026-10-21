#!/usr/bin/env python3
"""Uniformiza a grafia da marca para ``LusoSofá``, com S maiúsculo.

Por defeito faz **dry-run**. Para escrever mesmo:

    python3 scripts_lusosofa/corrigir_grafia_marca.py --aplicar

Decisão de 2026-09-25. A grafia com S maiúsculo é a que o rodapé já usava e a
que a própria página de Facebook da empresa usa (``facebook.com/LusoSofa/``);
era o resto do site que estava inconsistente.

**Não toca no nome legal da empresa** (``Lusosofá — Feel the Confort, Lda.``).
Esse é nome registado, sai em faturas e documentos fiscais, e alterá-lo não é
uma questão de coerência visual. Fica para decisão expressa.

`FACTO OBSERVADO` (2026-09-25), e é o que obriga à segunda metade do script:
mudar o texto de origem de um campo traduzido por termo **não deixa as
traduções órfãs**, como seria de esperar. O Odoo remapeia-as para o novo termo
de origem — e, ao fazê-lo, **grava o texto antigo como tradução da língua de
origem**. O resultado é que a página passa a ter uma tradução pt_PT explícita
com a grafia errada, a sobrepor-se a uma origem já corrigida, e a correcção
não aparece em lado nenhum.

Por isso não basta corrigir a origem: é preciso corrigir também os valores
traduzidos, em todas as línguas. É o que o passo 4 faz.
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

ERRADA = "Lusosofá"
CERTA = "LusoSofá"

# Nome legal: intencionalmente fora.
NOME_LEGAL = "Lusosofá — Feel the Confort, Lda."


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true", help="escreve mesmo")
    ap.add_argument("--creds", default=os.path.expanduser("~/.lusosofa_odoo.json"))
    args = ap.parse_args()

    odoo = Odoo(json.load(open(args.creds, encoding="utf-8")))
    modo = "APLICAR" if args.aplicar else "dry-run (não escreve nada)"
    print(f"\nGrafia da marca -> {CERTA} [{modo}]")
    print(f"{odoo.url} · base {odoo.db}\n")

    site = odoo.search_read("website", [], ["id", "name"])[0]
    vistas = odoo.kw("ir.ui.view", "search_read",
                     [[["arch_db", "like", ERRADA], ["website_id", "!=", False]]],
                     {"fields": ["id", "key", "name"]})

    print("1. nome do website")
    muda_site = site["name"] and ERRADA in site["name"]
    print(f"   {site['name']!r}" + (f" -> {site['name'].replace(ERRADA, CERTA)!r}"
                                    if muda_site else "  (já correcto)"))

    print("\n2. páginas")
    trabalho = []
    for v in vistas:
        arch = odoo.kw("ir.ui.view", "read", [[v["id"]], ["arch_db"]],
                       {"context": {"lang": "en_US"}})[0]["arch_db"] or ""
        n = arch.count(ERRADA)
        if n:
            trabalho.append((v["id"], v["key"] or v["name"], arch, n))
            print(f"   id={v['id']:5} {(v['key'] or v['name'])[:38]:40} {n} ocorrência(s)")

    print("\n3. deixado de fora, de propósito")
    empresa = odoo.search_read("res.company", [], ["name"])[0]
    print(f"   nome legal da empresa: {empresa['name']!r}")
    print("   (nome registado, sai em faturas — precisa de decisão expressa)")

    # Todas as vistas com traduções, não só as que têm a grafia na origem: o
    # texto antigo pode já estar gravado como valor traduzido de uma correcção
    # anterior, e nesse caso a origem está certa e a página continua errada.
    print("\n4. valores traduzidos com a grafia antiga")
    traducoes = {}
    todas = {v["id"] for v in vistas} | {vid for vid, _, _, _ in trabalho}
    for vid in sorted(todas):
        termos = odoo.kw("ir.ui.view", "get_field_translations", [[vid], "arch_db"])[0]
        porlingua = {}
        for t in termos:
            if t.get("value") and ERRADA in t["value"]:
                porlingua.setdefault(t["lang"], {})[t["source"]] = \
                    t["value"].replace(ERRADA, CERTA)
        if porlingua:
            traducoes[vid] = porlingua
            for lang, m in porlingua.items():
                print(f"   id={vid} {lang}: {len(m)} valor(es)")
    if not traducoes:
        print("   nenhum")

    if not args.aplicar:
        print("\n  Nada foi escrito. Para aplicar: --aplicar\n")
        return

    carimbo = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    destino = RAIZ / f".backup_lusosofa_grafia_{carimbo}.json"
    destino.write_text(json.dumps({
        "tirado_em_utc": carimbo, "base": odoo.db, "url": odoo.url,
        "accao": f"grafia da marca {ERRADA} -> {CERTA}",
        "website_nome_antes": site["name"],
        "vistas_antes": {str(vid): arch for vid, _, arch, _ in trabalho},
        "traducoes_antes": {
            str(vid): odoo.kw("ir.ui.view", "get_field_translations", [[vid], "arch_db"])[0]
            for vid, _, _, _ in trabalho
        },
        "como_reverter": "repor arch_db de cada vista e o nome do website",
    }, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"\n  resguardo: {destino.name}")

    if muda_site:
        odoo.kw("website", "write", [[site["id"]], {"name": site["name"].replace(ERRADA, CERTA)}])
        print(f"  website: {site['name']} -> {site['name'].replace(ERRADA, CERTA)}")
    for vid, chave, arch, n in trabalho:
        odoo.kw("ir.ui.view", "write", [[vid], {"arch_db": arch.replace(ERRADA, CERTA)}],
                {"context": {"lang": "en_US"}})
        print(f"  {chave}: {n} ocorrência(s) corrigidas na origem")

    # Relê depois de escrever a origem: é a escrita anterior que cria os
    # valores traduzidos com o texto antigo, pelo que a lista calculada antes
    # dela está incompleta por construção.
    for vid in sorted(todas):
        termos = odoo.kw("ir.ui.view", "get_field_translations", [[vid], "arch_db"])[0]
        porlingua = {}
        for t in termos:
            if t.get("value") and ERRADA in t["value"]:
                porlingua.setdefault(t["lang"], {})[t["source"]] = \
                    t["value"].replace(ERRADA, CERTA)
        for lang, m in porlingua.items():
            odoo.kw("ir.ui.view", "update_field_translations", [[vid], "arch_db", {lang: m}])
            print(f"  id={vid} {lang}: {len(m)} valor(es) traduzido(s) corrigidos")

    print("\nverificação — contra as páginas servidas, nas duas línguas")
    ok = True
    for u in ["/", "/about-us", "/contactus", "/es", "/es/about-us"]:
        p = urllib.request.urlopen(odoo.url + u, timeout=90).read().decode("utf-8", "replace")
        corpo = re.sub(r"<script.*?</script>", "", p, flags=re.S)
        restam = len(re.findall(re.escape(ERRADA), corpo)) - corpo.count(NOME_LEGAL)
        restam = max(restam, 0)
        marca = "  " if restam == 0 else "! "
        print(f"{marca}{u:16} {CERTA}: {corpo.count(CERTA):2}   "
              f"{ERRADA} fora do nome legal: {restam}")
        ok = ok and restam == 0

    print("\n" + ("Grafia uniformizada nas duas línguas." if ok else
                  "ATENÇÃO: restam ocorrências. Vê o resguardo."))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
