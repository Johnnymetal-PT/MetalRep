#!/usr/bin/env python3
"""Tira a fotografia de origem do Odoo do topo da página de contactos.

Por defeito faz **dry-run**. Para escrever mesmo:

    python3 scripts_lusosofa/arrumar_topo_contactos.py --aplicar

## O que está lá e porque sai

`FACTO OBSERVADO` (2026-09-28): a página de contactos abre com o bloco
`s_title parallax` do Odoo, e a imagem de fundo é
`/web/image/website.s_parallax_default_image` — **a fotografia de exemplo que o
Odoo traz de origem**, um tecto de escritório sem relação nenhuma com estofos.
Por cima leva dois filtros pretos a 50%, que a deixam cinzenta e baça.

Não é uma questão de gosto isolada: é a **única página do site com este
padrão**. As outras duas abrem com sobretítulo e título sobre o preto da marca,
sem imagem:

    /about-us   <span class="pg-eyebrow">A nossa história</span><h1>Sobre nós</h1>
    /projetos   <span class="pg-eyebrow">Trabalho por encomenda</span><h1>Projetos à medida</h1>

A de contactos fica igual às irmãs. Isto é a mesma direcção das decisões
anteriores — fora as molduras de linho, fora a faixa dourada, fora os itálicos:
tirar ornamento que não diz nada e deixar o tipo respirar.

Trocar a fotografia por uma da LusoSofá era a outra saída possível, e foi
descartada: a página de contactos existe para alguém escrever uma mensagem, e
uma fotografia grande no topo só empurra o formulário para baixo da dobra.

## Cuidado com a língua

A arquitetura escreve-se em contexto `en_US`, que é a língua-fonte. Escrevê-la
na língua do site faz o Odoo guardar o texto antigo como **tradução** e o site
passa a servir duas versões da mesma página — já aconteceu duas vezes neste
projeto. O sobretítulo novo leva tradução espanhola à parte.
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

URL = "/contactus"

# O mesmo padrão de /projetos, incluindo o filete. O título não muda.
TOPO_NOVO = (
    '<section class="s_text_block pt64 pb24 o_cc o_cc1" '
    'data-snippet="s_text_block" data-name="Título">'
    '<div class="container">'
    '<span class="pg-eyebrow">Fale connosco</span>'
    '<h1>Contacte-nos</h1>'
    '<hr class="pg-rule"/>'
    '</div></section>'
)

ESPANHOL = {'<span class="pg-eyebrow">Fale connosco</span>':
            '<span class="pg-eyebrow">Hable con nosotros</span>'}

# O que tem de desaparecer da página servida, e o que tem de continuar lá.
SAI = ["s_parallax_default_image", "s_parallax_is_fixed"]
FICA = ["s_website_form", "Contacte-nos", "lusosofa@gmail.com", "255 181 731"]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true", help="escreve mesmo")
    ap.add_argument("--creds", default=os.path.expanduser("~/.lusosofa_odoo.json"))
    args = ap.parse_args()

    odoo = Odoo(json.load(open(args.creds, encoding="utf-8")))
    modo = "APLICAR" if args.aplicar else "dry-run (não escreve nada)"
    print(f"\nTopo da página de contactos [{modo}]")
    print(f"{odoo.url} · base {odoo.db}\n")

    pagina = odoo.search_read("website.page", [["url", "=", URL]], ["id", "view_id"])
    if not pagina:
        raise SystemExit(f"ABORTADO: não encontrei a página {URL}.")
    vista = pagina[0]["view_id"][0]

    arch = odoo.kw("ir.ui.view", "read", [[vista], ["arch_db"]],
                   {"context": {"lang": "en_US"}})[0]["arch_db"]

    antigo = re.search(r"(?s)<section\b.*?</section>", arch)
    if not antigo:
        raise SystemExit("ABORTADO: não encontrei a primeira secção da página.")
    antigo = antigo.group(0)

    if "s_parallax" not in antigo:
        print("  a secção de topo já não tem a imagem do Odoo — nada a fazer")
        print(f"  actual: {re.sub(chr(32) + '+', chr(32), antigo)[:160]}")
        return

    compacto = re.sub(r"\s+", " ", antigo)
    print("  sai:")
    print(f"    {compacto[:190]}")
    print("\n  entra:")
    print(f"    {TOPO_NOVO[:190]}")
    print(f"\n  sobretítulo novo em espanhol: {list(ESPANHOL.values())[0]}")

    if not args.aplicar:
        print("\n  Nada foi escrito. Para aplicar: --aplicar\n")
        return

    carimbo = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    destino = RAIZ / f".backup_lusosofa_topo_contactos_{carimbo}.json"
    destino.write_text(json.dumps({
        "tirado_em_utc": carimbo, "base": odoo.db, "url": odoo.url,
        "accao": "substituir o topo parallax da página de contactos",
        "vista": vista, "arch_db_antes": arch,
        "como_reverter": "escrever de volta arch_db_antes em contexto en_US",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n  resguardo: {destino.name}")

    odoo.kw("ir.ui.view", "write", [[vista], {"arch_db": arch.replace(antigo, TOPO_NOVO)}],
            {"context": {"lang": "en_US"}})
    print(f"  topo substituído na vista {vista}")
    odoo.kw("ir.ui.view", "update_field_translations", [[vista], "arch_db", {"es_ES": ESPANHOL}])
    print("  sobretítulo traduzido para espanhol")

    print("\nverificação — contra as páginas servidas")
    ok = True
    for u in [URL, "/es" + URL]:
        r = urllib.request.urlopen(odoo.url + u, timeout=90)
        h = r.read().decode("utf-8", "replace")
        faltam = [x for x in FICA if x not in h and not (x == "Contacte-nos" and "/es" in u)]
        restos = [x for x in SAI if x in h]
        print(f"  {u:16} HTTP {r.status}")
        if restos:
            print(f"    ! ainda tem: {restos}")
            ok = False
        if faltam:
            print(f"    ! deixou de ter: {faltam}")
            ok = False
    es = urllib.request.urlopen(odoo.url + "/es" + URL, timeout=90).read().decode("utf-8", "replace")
    if "Hable con nosotros" not in es:
        print("    ! o sobretítulo espanhol não apareceu")
        ok = False
    else:
        print("  sobretítulo espanhol na página: sim")

    print("\n" + ("Topo arrumado." if ok else "ATENÇÃO: algo não confere. Vê o resguardo."))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
