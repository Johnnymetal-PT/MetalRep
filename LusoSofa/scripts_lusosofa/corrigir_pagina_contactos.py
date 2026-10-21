#!/usr/bin/env python3
"""Corrige a página de contactos da LusoSofá.

Por defeito faz **dry-run**. Para escrever mesmo:

    python3 scripts_lusosofa/corrigir_pagina_contactos.py --aplicar

Três defeitos, encontrados a 2026-09-26. O primeiro não é cosmético.

**1. O formulário enviava para o endereço de exemplo do Odoo.**
O campo oculto ``email_to`` do formulário tinha ``info@yourcompany.example.com``
— o valor que o Odoo põe por defeito e que ninguém trocou. O formulário cria
um ``mail.mail`` para esse destino, ou seja, **todas as mensagens enviadas pelo
site iam para um domínio que não existe**. Nada no site o denunciava: o
visitante vê a confirmação de envio na mesma.

Vale a pena dizer o que isto não permite saber: quantas mensagens se perderam,
e de quem. O que ficou por entregar não deixou rasto no site.

**2. Código postal antigo.** A página mostrava ``4590-241``; o registo da
empresa diz ``4590-196``. O rodapé já tinha sido alinhado a 2026-09-25 — esta
página tinha o valor numa vista própria e ficou de fora.

**3. O mapa procurava pelo nome, não pela morada.** O ``iframe`` do Google Maps
tinha ``q=Lusosofá``, o que devolve o que o Google achar que é a empresa. Passa
a apontar para a morada concreta.

O formulário fica a enviar para o mesmo endereço que o site já publica no
rodapé — não se inventa um destino novo.
"""

import argparse
import datetime
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aplicar_identidade import Odoo, RAIZ  # noqa: E402

URL = "/contactus"
EXEMPLO_ODOO = "info@yourcompany.example.com"
CP_ANTIGO = "4590-241"


def vista_servida(odoo, url):
    """Qual das páginas com este URL é a que o site serve.

    Há duas em ``/contactus``: a escrita pela LusoSofá e o template por defeito
    do Odoo, com morada e email de exemplo. Escolher pelo id mais baixo ou pela
    data daria a errada, por isso compara-se o texto de cada uma com a página
    que o servidor entrega.
    """
    def texto(s):
        s = re.sub(r"<(script|style).*?</\1>", "", s, flags=re.S)
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()

    servido = texto(urllib.request.urlopen(odoo.url + url, timeout=90).read().decode("utf-8", "replace"))
    melhor, pontos = None, -1
    for p in odoo.search_read("website.page", [["url", "=", url]], ["id", "view_id"]):
        arch = odoo.kw("ir.ui.view", "read", [[p["view_id"][0]], ["arch_db"]],
                       {"context": {"lang": "pt_PT"}})[0]["arch_db"] or ""
        palavras = {w for w in re.findall(r"[A-Za-zÀ-ÿ]{8,}", texto(arch))}
        n = sum(1 for w in palavras if w in servido)
        frac = n / len(palavras) if palavras else 0
        print(f"   página {p['id']:3} vista {p['view_id'][0]:5}: {n}/{len(palavras)} "
              f"palavras distintivas na página servida ({frac:.0%})")
        if n > pontos:
            melhor, pontos = p, n
    if not melhor or pontos == 0:
        raise SystemExit("ABORTADO: não consegui determinar qual a página servida.")
    return melhor


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true", help="escreve mesmo")
    ap.add_argument("--creds", default=os.path.expanduser("~/.lusosofa_odoo.json"))
    args = ap.parse_args()

    odoo = Odoo(json.load(open(args.creds, encoding="utf-8")))
    modo = "APLICAR" if args.aplicar else "dry-run (não escreve nada)"
    print(f"\nPágina de contactos [{modo}]")
    print(f"{odoo.url} · base {odoo.db}\n")

    empresa = odoo.search_read("res.company", [], ["email", "zip", "city", "street"])[0]
    print("  dados do registo da empresa:")
    print(f"    email {empresa['email']} · {empresa['street']}, {empresa['zip']} {empresa['city']}")
    if not empresa["email"]:
        raise SystemExit("ABORTADO: a empresa não tem email — não há destino para o formulário.")

    print("\n  qual das páginas é servida:")
    pag = vista_servida(odoo, URL)
    vid = pag["view_id"][0]
    antes = odoo.kw("ir.ui.view", "read", [[vid], ["arch_db"]],
                    {"context": {"lang": "en_US"}})[0]["arch_db"]
    print(f"   -> página {pag['id']}, vista {vid}")

    depois = antes
    print("\n1. destino do formulário")
    achados = re.findall(r'name="email_to"[^>]*value="([^"]*)"', depois)
    for v in achados:
        print(f"   email_to = {v}" + ("   <- exemplo do Odoo" if v == EXEMPLO_ODOO else ""))
    if not achados:
        print("   ! não encontrei nenhum campo email_to nesta página")
    depois = re.sub(r'(name="email_to"[^>]*value=")[^"]*(")',
                    lambda m: m.group(1) + empresa["email"] + m.group(2), depois)
    novos = re.findall(r'name="email_to"[^>]*value="([^"]*)"', depois)
    if novos != achados:
        print(f"   -> {empresa['email']}")

    print("\n2. código postal")
    n_cp = depois.count(CP_ANTIGO)
    print(f"   {CP_ANTIGO}: {n_cp} ocorrência(s)" +
          (f" -> {empresa['zip']}" if n_cp else "  (já alinhado)"))
    depois = depois.replace(CP_ANTIGO, empresa["zip"])

    print("\n3. mapa")
    morada = f"{empresa['street']}, {empresa['zip']} {empresa['city']}, Portugal"
    def trocar_q(m):
        return m.group(1) + urllib.parse.quote(morada) + m.group(3)
    antes_mapa = re.findall(r'(s_map_embedded[^>]*src="[^"]*?[?&]q=)([^&"]*)(&)', depois)
    for _, q, _ in antes_mapa:
        print(f"   q={urllib.parse.unquote(q)!r} -> {morada!r}")
    depois = re.sub(r'(s_map_embedded[^>]*src="[^"]*?[?&]q=)([^&"]*)(&)', trocar_q, depois)
    if not antes_mapa:
        print("   (sem mapa nesta página)")

    mudou_origem = depois != antes
    if mudou_origem:
        try:
            xml.dom.minidom.parseString(depois)
        except Exception as e:
            raise SystemExit(f"ABORTADO: o resultado não é XML válido — {e}")
        print(f"\n  vista: {len(antes)} -> {len(depois)} caracteres, XML válido")
    else:
        print("\n  a origem já está correcta")

    # Os valores traduzidos levantam-se sempre, mude ou não a origem: é
    # precisamente quando a origem já está boa que o texto antigo sobrevive
    # escondido numa tradução, e é esse o caso que passa despercebido.
    trocas = [(EXEMPLO_ODOO, empresa["email"]), (CP_ANTIGO, empresa["zip"])]

    def levantar():
        por_lingua = {}
        for t in odoo.kw("ir.ui.view", "get_field_translations", [[vid], "arch_db"])[0]:
            if not t.get("value"):
                continue
            novo = t["value"]
            for velho, certo in trocas:
                novo = novo.replace(velho, certo)
            if novo != t["value"]:
                por_lingua.setdefault(t["lang"], {})[t["source"]] = novo
        return por_lingua

    print("\n4. valores traduzidos com o texto antigo")
    pendentes = levantar()
    for lang, m in pendentes.items():
        print(f"   {lang}: {len(m)} valor(es)")
    if not pendentes:
        print("   nenhum")

    if not mudou_origem and not pendentes:
        print("\n  Nada a mudar.\n")
        return

    if not args.aplicar:
        print("\n  Nada foi escrito. Para aplicar: --aplicar\n")
        return

    carimbo = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    destino = RAIZ / f".backup_lusosofa_contactos_{carimbo}.json"
    destino.write_text(json.dumps({
        "tirado_em_utc": carimbo, "base": odoo.db, "url": odoo.url,
        "accao": "corrigir destino do formulário, código postal e mapa",
        "pagina": pag, "vista": vid, "arch_db_antes": antes,
        "email_to_antes": achados,
        "como_reverter": f"ir.ui.view write [[{vid}], {{'arch_db': <arch_db_antes>}}] com lang en_US",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n  resguardo: {destino.name}")

    if mudou_origem:
        odoo.kw("ir.ui.view", "write", [[vid], {"arch_db": depois}],
                {"context": {"lang": "en_US"}})
        print("  origem escrita")

    # Escrever a origem não chega, e esta é a segunda vez que isto morde.
    #
    # Num campo traduzido por termo, mudar a origem faz o Odoo remapear as
    # traduções existentes para o novo termo — e gravar o texto antigo como
    # tradução, incluindo na própria língua de origem. O valor traduzido passa
    # a tapar a origem corrigida, e a página continua a mostrar o texto velho
    # sem que nada assinale o problema.
    #
    # Por isso, depois de escrever, varrem-se os valores traduzidos à procura
    # do que se acabou de corrigir.
    # Relê depois de escrever: é a escrita da origem que cria os valores
    # traduzidos com o texto antigo, pelo que o levantamento feito antes dela
    # está incompleto por construção.
    for lang, mapa in levantar().items():
        odoo.kw("ir.ui.view", "update_field_translations", [[vid], "arch_db", {lang: mapa}])
        print(f"  {lang}: {len(mapa)} valor(es) traduzido(s) corrigidos")

    print("\nverificação — contra as páginas servidas, nas duas línguas")
    ok = True
    for lingua, caminho in [("pt", URL), ("es", "/es" + URL)]:
        p = urllib.request.urlopen(odoo.url + caminho, timeout=90).read().decode("utf-8", "replace")
        corpo = re.sub(r"<footer.*?</footer>", "", p, flags=re.S)
        for alvo, o_que, quer in [
            (EXEMPLO_ODOO, "endereço de exemplo do Odoo", False),
            (empresa["email"], "destino do formulário", True),
            (CP_ANTIGO, "código postal antigo", False),
            (empresa["zip"], "código postal do registo", True),
        ]:
            tem = alvo in corpo
            marca = "  " if tem == quer else "! "
            print(f"{marca}[{lingua}] {o_que:32} {'presente' if tem else 'ausente'}")
            ok = ok and tem == quer

    print("\n" + ("Página de contactos corrigida." if ok else
                  "ATENÇÃO: algo não confere. Vê o resguardo."))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
