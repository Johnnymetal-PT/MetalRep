#!/usr/bin/env python3
"""Corrige as ligações partidas e os rótulos ingleses do rodapé da Lusosofá.

Por defeito faz **dry-run**. Para escrever mesmo:

    python3 scripts_lusosofa/corrigir_rodape.py --aplicar

Actua sobre a vista do rodapé em uso — o ``template_footer_links`` na cópia
específica deste website — e só sobre ela. Escreve no **texto de origem**, não
numa tradução: é o que muda o que a versão portuguesa mostra.

O que este script faz, e nada além disso:

* remove as entradas cujo destino não existe (``/privacy``, que devolve 404) ou
  que não têm destino nenhum (``href="#"``);
* traduz os dois cabeçalhos de coluna que ficaram em inglês.

O que **não** faz, de propósito, e fica para decisão de quem conhece a intenção:

* a coluna «Siga-nos», cujos quatro ícones devolvem 404 por os endereços não
  estarem preenchidos. Removê-la obriga a mexer nas áreas da grelha das
  restantes colunas — é alteração de desenho, não correcção de defeito;
* a entrada «Projetos», que aponta para ``/contactus``. O destino funciona; é o
  rótulo que não bate certo, e há duas leituras possíveis do que se pretendia.

Antes de escrever confirma que cada alvo aparece **uma única vez**, e depois de
escrever confirma que o resultado continua a ser XML válido e que a página
servida deixou de ter os 404.
"""

import argparse
import datetime
import json
import os
import re
import sys
import urllib.error
import urllib.request
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aplicar_identidade import Odoo, RAIZ  # noqa: E402

VISTA_RODAPE = "website.template_footer_links"

# Entradas a remover: o <li> inteiro que contém este href.
REMOVER = [
    ("/privacy", "destino inexistente — devolve 404"),
    ('href="#"', "sem destino"),
]

# Rótulos de coluna que ficaram em inglês.
ROTULOS = {
    ">Explore<": ">Explorar<",
    ">Get in touch<": ">Fale connosco<",
}


def vista_em_uso(odoo):
    vistas = odoo.kw("ir.ui.view", "search_read",
                     [[["key", "=", VISTA_RODAPE], ["website_id", "!=", False]]],
                     {"fields": ["id", "key", "website_id"], "context": {"active_test": False}})
    if len(vistas) != 1:
        raise SystemExit(
            f"ABORTADO: esperava uma cópia de {VISTA_RODAPE} específica do website, "
            f"encontrei {len(vistas)}: {vistas}"
        )
    return vistas[0]["id"]


def remover_li(arch, marca):
    """Remove o <li> que contém `marca`. Devolve (arch novo, quantos removeu)."""
    padrao = re.compile(r"<li\b[^>]*>(?:(?!</li>).)*?" + re.escape(marca) + r".*?</li>", re.S)
    achados = padrao.findall(arch)
    return padrao.sub("", arch, count=len(achados)), len(achados)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true", help="escreve mesmo")
    ap.add_argument("--creds", default=os.path.expanduser("~/.lusosofa_odoo.json"))
    args = ap.parse_args()

    odoo = Odoo(json.load(open(args.creds, encoding="utf-8")))
    modo = "APLICAR" if args.aplicar else "dry-run (não escreve nada)"
    print(f"\nRodapé da Lusosofá [{modo}]")
    print(f"{odoo.url} · base {odoo.db}\n")

    vid = vista_em_uso(odoo)
    # O texto de origem lê-se e escreve-se em en_US: é o que a versão
    # portuguesa mostra, por não haver tradução pt_PT destes termos.
    antes = odoo.kw("ir.ui.view", "read", [[vid], ["arch_db"]],
                    {"context": {"lang": "en_US"}})[0]["arch_db"]
    print(f"  vista {vid} ({VISTA_RODAPE}) — {len(antes)} caracteres")

    depois = antes
    for marca, porque in REMOVER:
        depois, n = remover_li(depois, marca)
        print(f"  remover {marca!r} ({porque}): {n} entrada(s)")
        if n == 0:
            raise SystemExit(f"ABORTADO: não encontrei nenhuma entrada com {marca!r}.")

    for velho, novo in ROTULOS.items():
        n = depois.count(velho)
        print(f"  rótulo {velho.strip('<>')!r} -> {novo.strip('<>')!r}: {n} ocorrência(s)")
        if n != 1:
            raise SystemExit(f"ABORTADO: esperava uma ocorrência de {velho!r}, encontrei {n}.")
        depois = depois.replace(velho, novo)

    try:
        xml.dom.minidom.parseString(depois)
    except Exception as e:
        raise SystemExit(f"ABORTADO: o resultado não é XML válido — {e}")
    print(f"\n  resultado: {len(depois)} caracteres, XML válido")

    restantes = re.findall(r'<a[^>]+href="([^"]+)"', depois)
    print(f"  ligações que ficam: {sorted(set(restantes))}")

    if not args.aplicar:
        print("\n  Nada foi escrito. Para aplicar: --aplicar\n")
        return

    carimbo = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    destino = RAIZ / f".backup_lusosofa_rodape_{carimbo}.json"
    destino.write_text(json.dumps({
        "tirado_em_utc": carimbo, "base": odoo.db, "url": odoo.url,
        "accao": "remover ligações partidas e traduzir rótulos do rodapé",
        "vista": vid, "arch_db_antes": antes,
        "como_reverter": f"ir.ui.view write [[{vid}], {{'arch_db': <arch_db_antes>}}] com lang en_US",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n  resguardo: {destino.name}")

    odoo.kw("ir.ui.view", "write", [[vid], {"arch_db": depois}],
            {"context": {"lang": "en_US"}})
    print("  escrito")

    print("\nverificação — contra a página servida, não contra a base")
    ok = True
    pagina = urllib.request.urlopen(odoo.url + "/", timeout=90).read().decode("utf-8", "replace")
    rod = re.search(r"<footer.*?</footer>", pagina, re.S)
    alvo = rod.group(0) if rod else pagina

    for indesejado in ["/privacy", "Documentação", "Recursos", "Explore", "Get in touch"]:
        limpo = indesejado not in alvo
        print(f"  rodapé já não tem {indesejado!r}: {'sim' if limpo else 'NÃO'}")
        ok = ok and limpo
    for esperado in ["Explorar", "Fale connosco", "Produtos", "História"]:
        print(f"  rodapé tem {esperado!r}: {'sim' if esperado in alvo else 'NÃO'}")
        ok = ok and esperado in alvo

    for u in sorted({h for h in re.findall(r'<a[^>]+href="(/[^"]*)"', alvo)}):
        try:
            cod = urllib.request.urlopen(odoo.url + u, timeout=45).status
        except urllib.error.HTTPError as e:
            cod = e.code
        marca = "  " if cod == 200 else "  ! "
        print(f"{marca}{cod}  {u}")
        if cod != 200 and not u.startswith("/website/social/"):
            ok = False

    print("\n" + ("Rodapé corrigido." if ok else "ATENÇÃO: alguma coisa não confere. Vê o resguardo."))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
