#!/usr/bin/env python3
"""Aplica decisões tomadas sobre o website da Lusosofá.

Por defeito faz **dry-run**. Para escrever mesmo:

    python3 scripts_lusosofa/aplicar_decisoes_site.py --aplicar

Cada bloco aqui corresponde a uma decisão de quem tem autoridade para a tomar,
registada com a data. Não são correcções técnicas — são escolhas, e é por isso
que ficam escritas em vez de aplicadas à mão e esquecidas.

Decisões de 2026-09-25:

* **Redes sociais** — foram fornecidos os endereços de Instagram e Facebook.
  Preenchem-se os campos do website, que é o que faz a rota ``/website/social/*``
  deixar de devolver 404. O X e o LinkedIn não têm endereço, e as entradas
  saem do rodapé: uma ligação sem destino é pior do que a ausência dela.

* **Código postal** — o rodapé dizia ``4590-241`` e o registo da empresa diz
  ``4590-196``. Alinha-se o rodapé pelo registo, por ser o dado confirmado a
  2026-09-21 e o que sai em documentos. Se o errado for o registo, é esta a
  linha a inverter.

* **Publicidade ao fornecedor** — o rodapé trazia duas ligações para o odoo.com.
  Desactiva-se a vista que as gera. Desactivar, não apagar: repõe-se ligando-a
  outra vez.

É idempotente: correr duas vezes dá o mesmo resultado que correr uma.
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

REDES = {
    "social_facebook": "https://www.facebook.com/LusoSofa/?locale=pt_PT",
    "social_instagram": "https://www.instagram.com/lusosofa/",
}

# Redes sem endereço fornecido: as entradas saem do rodapé.
REDES_SEM_ENDERECO = ["twitter", "linkedin"]

CODIGO_POSTAL_ERRADO = "4590-241"
VISTA_RODAPE = "website.template_footer_links"
VISTA_PUBLICIDADE = "website.brand_promotion"


class SemRedireccao(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def destino_de(url):
    """Para onde aponta uma rota, sem seguir o redireccionamento."""
    abridor = urllib.request.build_opener(SemRedireccao)
    try:
        with abridor.open(url, timeout=45) as r:
            return r.status, r.headers.get("Location")
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Location")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true", help="escreve mesmo")
    ap.add_argument("--creds", default=os.path.expanduser("~/.lusosofa_odoo.json"))
    args = ap.parse_args()

    odoo = Odoo(json.load(open(args.creds, encoding="utf-8")))
    modo = "APLICAR" if args.aplicar else "dry-run (não escreve nada)"
    print(f"\nDecisões sobre o website [{modo}]")
    print(f"{odoo.url} · base {odoo.db}\n")

    site = odoo.search_read("website", [], ["id"] + list(REDES))[0]
    vistas = odoo.kw("ir.ui.view", "search_read",
                     [[["key", "=", VISTA_RODAPE], ["website_id", "!=", False]]],
                     {"fields": ["id"], "context": {"active_test": False}})
    if len(vistas) != 1:
        raise SystemExit(f"ABORTADO: esperava uma cópia de {VISTA_RODAPE}, achei {len(vistas)}.")
    vid = vistas[0]["id"]
    antes = odoo.kw("ir.ui.view", "read", [[vid], ["arch_db"]],
                    {"context": {"lang": "en_US"}})[0]["arch_db"]

    print("1. redes sociais")
    por_escrever = {c: v for c, v in REDES.items() if site.get(c) != v}
    for c, v in REDES.items():
        estado = "já está" if c not in por_escrever else f"{site.get(c) or 'vazio'} -> {v}"
        print(f"   {c:20} {estado}")

    depois = antes
    print("\n2. entradas sem endereço a remover do rodapé")
    for rede in REDES_SEM_ENDERECO:
        padrao = re.compile(r"<li\b[^>]*>(?:(?!</li>).)*?/website/social/" + rede + r".*?</li>", re.S)
        n = len(padrao.findall(depois))
        depois = padrao.sub("", depois)
        print(f"   {rede:12} {n} entrada(s)")

    print("\n3. código postal")
    n_cp = depois.count(CODIGO_POSTAL_ERRADO)
    empresa = odoo.search_read("res.company", [], ["zip"])[0]
    print(f"   registo da empresa: {empresa['zip']}   rodapé: "
          f"{CODIGO_POSTAL_ERRADO if n_cp else '(já alinhado)'}")
    if n_cp:
        depois = depois.replace(CODIGO_POSTAL_ERRADO, empresa["zip"])

    print("\n4. publicidade ao fornecedor")
    pub = odoo.kw("ir.ui.view", "search_read", [[["key", "=", VISTA_PUBLICIDADE]]],
                  {"fields": ["id", "active"], "context": {"active_test": False}})
    if not pub:
        print(f"   ! não encontrei {VISTA_PUBLICIDADE}")
    else:
        print(f"   {VISTA_PUBLICIDADE} (id {pub[0]['id']}): "
              f"{'activa — seria desactivada' if pub[0]['active'] else 'já desactivada'}")

    if depois != antes:
        try:
            xml.dom.minidom.parseString(depois)
        except Exception as e:
            raise SystemExit(f"ABORTADO: o rodapé deixaria de ser XML válido — {e}")
        print(f"\n   rodapé: {len(antes)} -> {len(depois)} caracteres, XML válido")

    if not args.aplicar:
        print("\n  Nada foi escrito. Para aplicar: --aplicar\n")
        return

    carimbo = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    destino = RAIZ / f".backup_lusosofa_decisoes_{carimbo}.json"
    destino.write_text(json.dumps({
        "tirado_em_utc": carimbo, "base": odoo.db, "url": odoo.url,
        "accao": "aplicar decisões de 2026-09-25 (redes, código postal, publicidade)",
        "website_antes": site,
        "vista_rodape": vid, "arch_db_antes": antes,
        "publicidade_antes": pub,
        "como_reverter": "repor arch_db, limpar os campos social_*, reactivar a vista",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n  resguardo: {destino.name}")

    if por_escrever:
        odoo.kw("website", "write", [[site["id"]], por_escrever])
        print(f"  escritos {len(por_escrever)} campos de redes sociais")
    if depois != antes:
        odoo.kw("ir.ui.view", "write", [[vid], {"arch_db": depois}],
                {"context": {"lang": "en_US"}})
        print("  rodapé escrito")
    if pub and pub[0]["active"]:
        odoo.kw("ir.ui.view", "write", [[pub[0]["id"]], {"active": False}])
        print(f"  {VISTA_PUBLICIDADE} desactivada")

    print("\nverificação — contra a página servida")
    ok = True
    pagina = urllib.request.urlopen(odoo.url + "/", timeout=90).read().decode("utf-8", "replace")
    rod = re.search(r"<footer.*?</footer>", pagina, re.S)
    alvo = rod.group(0) if rod else pagina

    for rede in REDES_SEM_ENDERECO:
        limpo = f"/website/social/{rede}" not in alvo
        print(f"  rodapé já não tem {rede}: {'sim' if limpo else 'NÃO'}")
        ok = ok and limpo

    for rede, url in REDES.items():
        rota = f"{odoo.url}/website/social/{rede.replace('social_', '')}"
        cod, para = destino_de(rota)
        certo = cod in (301, 302, 303, 307, 308) and para and url.split("?")[0] in para
        print(f"  {rota.rsplit('/', 1)[-1]:10} HTTP {cod} -> {para}")
        ok = ok and certo

    cp_ok = CODIGO_POSTAL_ERRADO not in alvo and empresa["zip"] in alvo
    print(f"  código postal {empresa['zip']} no rodapé: {'sim' if cp_ok else 'NÃO'}")
    ok = ok and cp_ok

    sem_odoo = "odoo.com" not in alvo
    print(f"  rodapé sem ligações para odoo.com: {'sim' if sem_odoo else 'NÃO'}")
    ok = ok and sem_odoo

    print("\n" + ("Decisões aplicadas." if ok else "ATENÇÃO: algo não confere. Vê o resguardo."))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
