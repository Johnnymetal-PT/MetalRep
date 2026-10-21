#!/usr/bin/env python3
"""Cria a página ``/projetos`` e aponta-lhe a entrada do rodapé.

Por defeito faz **dry-run**. Para escrever mesmo:

    python3 scripts_lusosofa/criar_pagina_projetos.py --aplicar

Decisão de 2026-09-25: a entrada «Projetos» do rodapé apontava para o
formulário de contacto, o que o rótulo nunca prometeu. Passa a apontar para
uma página sobre trabalho por encomenda.

**De onde vem o texto.** Inteiramente da página «Sobre nós» da própria
LusoSofá — os parágrafos sobre desenvolvimento para designers, sobre capitoné
e sobre restauro. Está reorganizado, não reescrito, e não há aqui uma única
afirmação de facto que a empresa não publique já: nada sobre prazos, materiais,
quantidades mínimas ou preços, que eu não tenho como saber.

A única frase minha é a chamada à acção no fim. Está assinalada no código para
quem rever saber o que confirmar.

É idempotente: se a página já existir, reescreve-lhe o conteúdo em vez de criar
uma segunda.
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

URL = "/projetos"
CHAVE = "website.projetos"
NOME = "Projetos"

# ── conteúdo ────────────────────────────────────────────────────────────────
# Cada parágrafo abaixo está textualmente na página «Sobre nós», excepto o
# bloco marcado como chamada à acção.

CORPO = """<t name="Projetos" t-name="website.projetos">
    <t t-call="website.layout">
        <div id="wrap" class="">
            <div class="oe_structure">
                <section class="s_text_block pt64 pb24 o_cc o_cc1" data-snippet="s_text_block" data-name="Título">
                    <div class="container">
                        <span class="pg-eyebrow">Trabalho por encomenda</span>
                        <h1>Projetos à medida</h1>
                        <hr class="pg-rule"/>
                    </div>
                </section>
                <section class="s_text_block pt32 pb32 o_cc o_cc1" data-snippet="s_text_block" data-name="Texto">
                    <div class="container">
                        <div class="row">
                            <div class="col-lg-9">
                                <p class="lead"><span>A LusoSofá dá forma às ideias e projetos dos designers, canalizando as suas energias criativas baseadas em diferentes raízes culturais, no desenvolvimento de produtos para indoor e outdoor para os segmentos residencial e Hotelaria. Esses produtos refletem a identidade LusoSofá, bem como a evolução dos hábitos de vida.</span></p>
                            </div>
                        </div>
                    </div>
                </section>
                <section class="s_text_block pt32 pb32 o_cc o_cc5" data-snippet="s_text_block" data-name="Capitoné">
                    <div class="container">
                        <div class="row">
                            <div class="col-lg-6">
                                <h2>Especialistas em capitoné</h2>
                                <hr class="pg-rule"/>
                                <p><span>Realizar trabalhos em capitoné é uma arte! O capitoné está de volta, versátil, elegante e sofisticado, cruza o clássico e o moderno e dá vida a qualquer produto.</span></p>
                            </div>
                            <div class="col-lg-6">
                                <h2>Restauro</h2>
                                <hr class="pg-rule"/>
                                <p><span>Se tem uma peça de grande valor sentimental, nós realizamos o seu restauro e damos-lhe uma vida nova, de elegância e bom gosto.</span></p>
                            </div>
                        </div>
                    </div>
                </section>
                <section class="s_text_block pt32 pb64 o_cc o_cc1" data-snippet="s_text_block" data-name="Contacto">
                    <div class="container text-center">
                        <!-- Chamada à acção: única redacção que não vem da página «Sobre nós». -->
                        <h2>Tem um projeto em mãos?</h2>
                        <p><span>Fale connosco sobre o que precisa.</span></p>
                        <p><a href="/contactus" class="btn btn-primary">Contacte-nos</a></p>
                    </div>
                </section>
            </div>
        </div>
    </t>
</t>"""

# ── tradução ────────────────────────────────────────────────────────────────
ESPANHOL = {
    "Trabalho por encomenda": "Trabajo por encargo",
    "Projetos à medida": "Proyectos a medida",
    "Especialistas em capitoné": "Especialistas en capitoné",
    "Restauro": "Restauración",
    "Tem um projeto em mãos?": "¿Tiene un proyecto entre manos?",
    "Contacte-nos": "Contáctenos",
    '<span>A LusoSofá dá forma às ideias e projetos dos designers, canalizando as suas energias criativas baseadas em diferentes raízes culturais, no desenvolvimento de produtos para indoor e outdoor para os segmentos residencial e Hotelaria. Esses produtos refletem a identidade LusoSofá, bem como a evolução dos hábitos de vida.</span>':
        '<span>LusoSofá da forma a las ideas y proyectos de los diseñadores, canalizando sus energías creativas, nacidas de distintas raíces culturales, en el desarrollo de productos de interior y exterior para los segmentos residencial y de hostelería. Estos productos reflejan la identidad LusoSofá, así como la evolución de los hábitos de vida.</span>',
    '<span>Realizar trabalhos em capitoné é uma arte! O capitoné está de volta, versátil, elegante e sofisticado, cruza o clássico e o moderno e dá vida a qualquer produto.</span>':
        '<span>¡Realizar trabajos en capitoné es un arte! El capitoné está de vuelta: versátil, elegante y sofisticado, cruza lo clásico y lo moderno y da vida a cualquier producto.</span>',
    '<span>Se tem uma peça de grande valor sentimental, nós realizamos o seu restauro e damos-lhe uma vida nova, de elegância e bom gosto.</span>':
        '<span>Si tiene una pieza de gran valor sentimental, la restauramos y le damos una vida nueva, de elegancia y buen gusto.</span>',
    '<span>Fale connosco sobre o que precisa.</span>':
        '<span>Hable con nosotros sobre lo que necesita.</span>',
}

VISTA_RODAPE = "website.template_footer_links"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true", help="escreve mesmo")
    ap.add_argument("--creds", default=os.path.expanduser("~/.lusosofa_odoo.json"))
    args = ap.parse_args()

    odoo = Odoo(json.load(open(args.creds, encoding="utf-8")))
    modo = "APLICAR" if args.aplicar else "dry-run (não escreve nada)"
    print(f"\nPágina {URL} [{modo}]")
    print(f"{odoo.url} · base {odoo.db}\n")

    xml.dom.minidom.parseString(CORPO.replace("t-call=", "data-t-call="))
    print(f"  conteúdo: {len(CORPO)} caracteres, XML válido")

    site = odoo.search_read("website", [], ["id"])[0]["id"]
    ja = odoo.search_read("website.page", [["url", "=", URL]], ["id", "view_id", "is_published"])
    print(f"  página existente: {ja or 'não'}")

    rodape = odoo.kw("ir.ui.view", "search_read",
                     [[["key", "=", VISTA_RODAPE], ["website_id", "!=", False]]],
                     {"fields": ["id"], "context": {"active_test": False}})[0]["id"]
    arch_rod = odoo.kw("ir.ui.view", "read", [[rodape], ["arch_db"]],
                       {"context": {"lang": "en_US"}})[0]["arch_db"]
    alvo = re.search(r'<a href="/contactus">(?:(?!</a>).)*?Projetos.*?</a>', arch_rod, re.S)
    print(f"  entrada 'Projetos' no rodapé aponta para /contactus: "
          f"{'sim' if alvo else 'NÃO — nada a repontar'}")

    if not args.aplicar:
        print("\n  Nada foi escrito. Para aplicar: --aplicar\n")
        return

    carimbo = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    destino = RAIZ / f".backup_lusosofa_projetos_{carimbo}.json"
    destino.write_text(json.dumps({
        "tirado_em_utc": carimbo, "base": odoo.db, "url": odoo.url,
        "accao": f"criar {URL} e repontar a entrada 'Projetos' do rodapé",
        "pagina_antes": ja, "rodape_id": rodape, "rodape_arch_antes": arch_rod,
        "como_reverter": f"despublicar {URL} e repor o arch_db do rodapé",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n  resguardo: {destino.name}")

    if ja:
        vid = ja[0]["view_id"][0]
        odoo.kw("ir.ui.view", "write", [[vid], {"arch_db": CORPO}],
                {"context": {"lang": "en_US"}})
        odoo.kw("website.page", "write", [[ja[0]["id"]],
                                          {"is_published": True, "website_indexed": True}])
        print(f"  conteúdo reescrito na vista {vid}")
    else:
        vid = odoo.kw("ir.ui.view", "create", [{
            "name": NOME, "type": "qweb", "mode": "primary", "key": CHAVE,
            "arch_db": CORPO, "website_id": site, "track": True,
        }], {"context": {"lang": "en_US"}})
        pid = odoo.kw("website.page", "create", [{
            "view_id": vid, "url": URL, "website_id": site,
            "is_published": True, "website_indexed": True,
        }])
        print(f"  criada: vista {vid}, página {pid}")

    odoo.kw("ir.ui.view", "update_field_translations", [[vid], "arch_db", {"es_ES": ESPANHOL}])
    print(f"  traduzidos {len(ESPANHOL)} termos para espanhol")

    if alvo:
        novo = alvo.group(0).replace('href="/contactus"', f'href="{URL}"')
        odoo.kw("ir.ui.view", "write",
                [[rodape], {"arch_db": arch_rod.replace(alvo.group(0), novo)}],
                {"context": {"lang": "en_US"}})
        print(f"  rodapé: 'Projetos' -> {URL}")

    print("\nverificação — contra as páginas servidas")
    ok = True
    for u in [URL, "/es" + URL]:
        p = urllib.request.urlopen(odoo.url + u, timeout=90)
        print(f"  {u:16} HTTP {p.status}")
        ok = ok and p.status == 200

    pt = urllib.request.urlopen(odoo.url + URL, timeout=90).read().decode("utf-8", "replace")
    for t in ["Projetos à medida", "Especialistas em capitoné", "Restauro"]:
        print(f"  {URL} tem {t!r}: {'sim' if t in pt else 'NÃO'}")
        ok = ok and t in pt

    es = urllib.request.urlopen(odoo.url + "/es" + URL, timeout=90).read().decode("utf-8", "replace")
    for t in ["Proyectos a medida", "Restauración", "hostelería"]:
        print(f"  /es{URL} tem {t!r}: {'sim' if t in es else 'NÃO'}")
        ok = ok and t in es

    home = urllib.request.urlopen(odoo.url + "/", timeout=90).read().decode("utf-8", "replace")
    rod = re.search(r"<footer.*?</footer>", home, re.S)
    aponta = f'href="{URL}"' in (rod.group(0) if rod else home)
    print(f"  rodapé aponta para {URL}: {'sim' if aponta else 'NÃO'}")
    ok = ok and aponta

    print("\n" + ("Página criada e ligada." if ok else "ATENÇÃO: algo não confere. Vê o resguardo."))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
