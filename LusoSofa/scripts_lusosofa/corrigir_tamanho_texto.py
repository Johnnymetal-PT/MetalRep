#!/usr/bin/env python3
"""Tira do texto corrido a classe de tamanho de título (``h5-fs``).

Por defeito faz **dry-run**. Para escrever mesmo:

    python3 scripts_lusosofa/corrigir_tamanho_texto.py --aplicar

O site queixava-se de letra grande de mais, e a causa não estava no tema: o
tamanho base é 16 px, mas os parágrafos das páginas vinham envolvidos em
``<span class="h5-fs">``, que o CSS do Odoo define em **25,5 px** — tamanho de
título aplicado a texto corrido. Doze vezes só na página inicial.

Quem montou as páginas no editor escolheu «tamanho 5» para o corpo do texto.
É uma escolha que se faz num menu e que nenhuma definição de tema desfaz:
baixar o tamanho base não mexe nos parágrafos, porque a classe ganha sempre.

O que este script remove é só a classe. O texto, a marcação e tudo o resto
ficam onde estavam, e os parágrafos passam a herdar o tamanho do tema — que é
onde a decisão deve viver.

`h1-fs` e `h3-fs` ficam: o primeiro é um título a sério, e os segundos são
parágrafos vazios usados como espaçamento.
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

CLASSE = "h5-fs"


def limpar(arch):
    """Tira `h5-fs` de cada atributo class, deixando as outras classes."""
    def troca(m):
        classes = [c for c in m.group(2).split() if c != CLASSE]
        if not classes:
            # Sem mais nenhuma classe, o atributo inteiro desaparece — deixar
            # `class=""` seria lixo que depois ninguém sabe se é intencional.
            return ""
        return f'{m.group(1)}class="{" ".join(classes)}"'
    return re.sub(r'(\s?)class="([^"]*\b' + re.escape(CLASSE) + r'\b[^"]*)"', troca, arch)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true", help="escreve mesmo")
    ap.add_argument("--creds", default=os.path.expanduser("~/.lusosofa_odoo.json"))
    args = ap.parse_args()

    odoo = Odoo(json.load(open(args.creds, encoding="utf-8")))
    modo = "APLICAR" if args.aplicar else "dry-run (não escreve nada)"
    print(f"\nTamanho do texto corrido [{modo}]")
    print(f"{odoo.url} · base {odoo.db}\n")

    vistas = odoo.kw("ir.ui.view", "search_read",
                     [[["arch_db", "like", CLASSE], ["website_id", "!=", False]]],
                     {"fields": ["id", "key", "name"]})

    trabalho = []
    for v in vistas:
        arch = odoo.kw("ir.ui.view", "read", [[v["id"]], ["arch_db"]],
                       {"context": {"lang": "en_US"}})[0]["arch_db"] or ""
        n = len(re.findall(r'class="[^"]*\b' + re.escape(CLASSE) + r'\b', arch))
        if n:
            trabalho.append((v["id"], v["key"] or v["name"], arch, n))
            print(f"  id={v['id']:5} {(v['key'] or v['name'])[:38]:40} {n} ocorrência(s)")
    if not trabalho:
        print("  nenhuma vista com a classe")

    def levantar():
        por_lingua = {}
        for vid, _, _, _ in trabalho:
            for t in odoo.kw("ir.ui.view", "get_field_translations", [[vid], "arch_db"])[0]:
                if not t.get("value") or CLASSE not in t["value"]:
                    continue
                por_lingua.setdefault((vid, t["lang"]), {})[t["source"]] = limpar(t["value"])
        return por_lingua

    print("\n  valores traduzidos com a mesma classe:")
    pendentes = levantar()
    for (vid, lang), m in pendentes.items():
        print(f"   id={vid} {lang}: {len(m)} valor(es)")
    if not pendentes:
        print("   nenhum")

    if not trabalho and not pendentes:
        print("\n  Nada a mudar.\n")
        return

    for vid, chave, arch, n in trabalho:
        novo = limpar(arch)
        try:
            xml.dom.minidom.parseString(novo)
        except Exception as e:
            raise SystemExit(f"ABORTADO: {chave} deixaria de ser XML válido — {e}")
    print(f"\n  {len(trabalho)} vista(s) continuam XML válido depois da limpeza")

    if not args.aplicar:
        print("\n  Nada foi escrito. Para aplicar: --aplicar\n")
        return

    carimbo = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    destino = RAIZ / f".backup_lusosofa_tamanho_{carimbo}.json"
    destino.write_text(json.dumps({
        "tirado_em_utc": carimbo, "base": odoo.db, "url": odoo.url,
        "accao": f"remover a classe {CLASSE} do texto corrido",
        "vistas_antes": {str(vid): arch for vid, _, arch, _ in trabalho},
        "traducoes_antes": {
            str(vid): odoo.kw("ir.ui.view", "get_field_translations", [[vid], "arch_db"])[0]
            for vid, _, _, _ in trabalho
        },
        "como_reverter": "repor arch_db de cada vista e os valores traduzidos",
    }, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"\n  resguardo: {destino.name}")

    for vid, chave, arch, n in trabalho:
        odoo.kw("ir.ui.view", "write", [[vid], {"arch_db": limpar(arch)}],
                {"context": {"lang": "en_US"}})
        print(f"  {chave}: {n} ocorrência(s) removidas da origem")

    for (vid, lang), mapa in levantar().items():
        odoo.kw("ir.ui.view", "update_field_translations", [[vid], "arch_db", {lang: mapa}])
        print(f"  id={vid} {lang}: {len(mapa)} valor(es) traduzido(s) corrigidos")

    print("\nverificação — contra as páginas servidas")
    ok = True
    for u in ["/", "/about-us", "/projetos", "/contactus",
              "/es", "/es/about-us", "/es/projetos"]:
        h = urllib.request.urlopen(odoo.url + u, timeout=90).read().decode("utf-8", "replace")
        n = len(re.findall(r"\b" + re.escape(CLASSE) + r"\b", h))
        marca = "  " if n == 0 else "! "
        print(f"{marca}{u:16} {CLASSE}: {n}")
        ok = ok and n == 0

    # O texto não pode ter desaparecido junto com a classe.
    #
    # As cadeias abaixo são copiadas da página, não escritas de memória: a
    # primeira versão deste teste procurava «A coleção Traços» e a página diz
    # «a coleção traços», em minúscula. Deu alarme sobre um site intacto, que é
    # a falha mais cara que uma verificação pode ter — depois do segundo susto
    # falso, deixa-se de a ler.
    h = urllib.request.urlopen(odoo.url + "/", timeout=90).read().decode("utf-8", "replace")
    for t in ["versatilidade e elegância", "A Nossa Seleção", "Descubra mais"]:
        print(f"  homepage mantém {t!r}: {'sim' if t in h else 'NÃO'}")
        ok = ok and t in h

    print("\n" + ("Texto corrido com o tamanho do tema." if ok else
                  "ATENÇÃO: algo não confere. Vê o resguardo."))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
