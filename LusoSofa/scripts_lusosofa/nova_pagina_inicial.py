#!/usr/bin/env python3
"""Reescreve a página inicial com a estrutura aprovada a 2026-09-28.

Por defeito faz **dry-run**. Para escrever mesmo:

    python3 scripts_lusosofa/nova_pagina_inicial.py --aplicar

## O que sai, e é preciso dizê-lo

A página anterior tinha uma **colagem de doze imagens** de tamanhos, épocas e
estilos diferentes — um Chesterfield ao lado de dois sofás turquesa, duas
banquetas, um pormenor cortado a sangrar pela margem, o logótipo sobre um fundo
de penas. Sem alinhamento nem escala comum. Era o maior problema visual do
site e é o motivo desta reescrita.

Sai também a secção **«A Nossa Seleção»**, com os quatro modelos Noa, Porto,
Estoril e Alcântara. Isso quer dizer que **esses três primeiros nomes deixam de
aparecer no site** — o Alcântara sobrevive no desenho. A alternativa era
mantê-los com as fotografias que têm, de 484 px, ao lado de imagens de 1400. A
decisão foi tomada a ver a maqueta; o resguardo repõe tudo.

## O que entra

Cinco secções, cada uma com uma coisa para dizer: capa, três imagens da mesma
proporção, faixa clara com o desenho do Alcântara, capitoné, contactos.

As cores vêm das combinações da paleta (``o_cc1``, ``o_cc2``, ``o_cc5``) e não
de valores fixos: assim acompanham a paleta e continuam a passar o critério AA,
que é verificado em cada implantação.

O texto vem da página «História» e das descrições já publicadas, encurtado. A
única redacção nova são as duas frases assinaladas em comentário.
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

CHAVE = "website.homepage"

# Uma imagem por sítio, e cada cartão com a peça que a categoria promete.
#
# A primeira versão repetia a imagem da capa no cartão dos sofás — o visitante
# desce meio ecrã e vê a mesma fotografia outra vez — e punha um **sofá** de
# canto debaixo do rótulo «Cadeirões». Nenhuma das duas se vê na maqueta; só
# aparecem com o site montado.
IMG = {
    "capa": "/web/image/2217",       # sala modular, 1536x1024 — a maior disponível
    "sofas": "/web/image/2220",      # seccional numa sala com arco
    "cadeiroes": "/web/image/2219",  # par de cadeirões terracota
    "quarto": "/web/image/2232",     # quarto com cabeceira em capitoné
    "desenho": "/web/image/2231",    # desenho assinado Alcântara
    "capitone": "/web/image/2236",   # cabeceira em capitoné, 1400x933
}


def moldura(url, alt, proporcao="4 / 3"):
    return (
        f'<div class="pg-frame"><div style="overflow: hidden; aspect-ratio: {proporcao};">'
        f'<img src="{url}" alt="{alt}" class="img img-fluid" loading="lazy" '
        f'style="width: 100%; height: 100%; object-fit: cover;"/></div></div>'
    )


CORPO = f"""<t name="Homepage" t-name="website.homepage">
    <t t-call="website.layout">
        <t t-set="pageName" t-value="'homepage'"/>
        <div id="wrap" class="oe_structure">
            <section class="s_text_block o_cc o_cc1 pt0 pb0" data-snippet="s_text_block" data-name="Capa">
                <div class="position-relative" style="min-height: 620px;">
                    <img src="{IMG['capa']}" alt="Sala ampla com sofá modular claro" class="w-100 h-100 position-absolute top-0 start-0" style="object-fit: cover; z-index: 0;" loading="eager"/>
                    <div class="position-absolute top-0 start-0 w-100 h-100 d-none d-lg-block" style="z-index: 1; background: linear-gradient(90deg, rgba(11,10,8,.88) 0%, rgba(11,10,8,.58) 44%, rgba(11,10,8,0) 74%);"/>
                    <div class="position-absolute top-0 start-0 w-100 h-100 d-lg-none" style="z-index: 1; background: linear-gradient(180deg, rgba(11,10,8,.62) 0%, rgba(11,10,8,.80) 55%, rgba(11,10,8,.92) 100%);"/>
                    <div class="container position-relative d-flex align-items-center" style="z-index: 2; min-height: 620px;">
                        <div class="col-lg-6">
                            <span class="pg-eyebrow">Estofos desde 2016 · Figueiró</span>
                            <h1 class="mt-3">Feito à medida do seu espaço</h1>
                            <p class="mt-4">Uma oficina artesanal que cresceu, e continua a dar forma às ideias de quem desenha.</p>
                            <div class="mt-4 d-flex flex-wrap gap-3">
                                <a href="/shop" class="btn btn-primary">Ver o catálogo</a>
                                <a href="/projetos" class="btn btn-outline-primary">Trabalho à medida</a>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
            <section class="s_text_block o_cc o_cc1 pt64 pb64" data-snippet="s_text_block" data-name="Categorias">
                <div class="container">
                    <div class="row align-items-end mb-4">
                        <div class="col-lg-8">
                            <span class="pg-eyebrow">O que fazemos</span>
                            <h2 class="mt-3">Sofás, cadeirões e quarto</h2>
                        </div>
                        <div class="col-lg-4 text-lg-end">
                            <a href="/shop">Ver os 12 artigos</a>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-12 col-md-4">
                            <a href="/shop/category/sofas-e-chaise-longues-1" class="text-decoration-none">
                                {moldura(IMG['sofas'], 'Sofá seccional numa sala ampla com arco')}
                            </a>
                            <p class="pg-eyebrow mt-3">Sofás e chaise longues</p>
                        </div>
                        <div class="col-12 col-md-4">
                            <a href="/shop/category/cadeiroes-2" class="text-decoration-none">
                                {moldura(IMG['cadeiroes'], 'Par de cadeirões de braços arredondados em tecido terracota')}
                            </a>
                            <p class="pg-eyebrow mt-3">Cadeirões</p>
                        </div>
                        <div class="col-12 col-md-4">
                            <a href="/shop/category/quarto-3" class="text-decoration-none">
                                {moldura(IMG['quarto'], 'Quarto com cama de cabeceira alta em capitoné')}
                            </a>
                            <p class="pg-eyebrow mt-3">Quarto</p>
                        </div>
                    </div>
                </div>
            </section>
            <section class="s_text_block o_cc o_cc2 pt64 pb64" data-snippet="s_text_block" data-name="Desenho">
                <div class="container">
                    <div class="row align-items-center">
                        <div class="col-lg-7">
                            {moldura(IMG['desenho'], 'Desenho a lápis de um sofá, assinado Alcântara', '3 / 2')}
                        </div>
                        <div class="col-lg-5 ps-lg-5 mt-4 mt-lg-0">
                            <span class="pg-eyebrow">Coleção Traços</span>
                            <h2 class="mt-3">Cada peça começa num traço</h2>
                            <p class="mt-4">A Coleção Traços vem demonstrar toda a versatilidade e elegância de uma linha criada a pensar em si. O conforto aliado a um design moderno e cativante vão poder fazer parte da sua casa.</p>
                            <p class="pg-signature">Deixe que o nosso traço embeleze o seu espaço.</p>
                            <p class="mt-4"><a href="/about-us">A nossa história</a></p>
                        </div>
                    </div>
                </div>
            </section>
            <section class="s_text_block o_cc o_cc5 pt64 pb64" data-snippet="s_text_block" data-name="Capitoné">
                <div class="container">
                    <div class="row align-items-center">
                        <div class="col-lg-5 order-lg-1 order-2 mt-4 mt-lg-0">
                            <span class="pg-eyebrow">Especialidade</span>
                            <h2 class="mt-3">Capitoné</h2>
                            <p class="mt-4">Versátil, elegante e sofisticado, cruza o clássico e o moderno e dá vida a qualquer produto.</p>
                            <p><a href="/projetos">Trabalho por encomenda</a></p>
                        </div>
                        <div class="col-lg-7 order-lg-2 order-1 ps-lg-5">
                            {moldura(IMG['capitone'], 'Cabeceira em capitoné verde-petróleo, com botão puxado em losangos', '3 / 2')}
                        </div>
                    </div>
                </div>
            </section>
            <section class="s_text_block o_cc o_cc1 pt64 pb64" data-snippet="s_text_block" data-name="Contactos">
                <div class="container">
                    <div class="row">
                        <div class="col-lg-5">
                            <span class="pg-eyebrow">Fale connosco</span>
                            <!-- Redacção nova, das duas únicas frases que não vêm de texto já publicado. -->
                            <h2 class="mt-3">Tem um projeto em mãos?</h2>
                            <p class="mt-4">Diga-nos o que precisa e respondemos com uma proposta.</p>
                            <p><a href="/contactus" class="btn btn-primary">Pedir orçamento</a></p>
                        </div>
                        <div class="col-lg-6 offset-lg-1 mt-5 mt-lg-0">
                            <p class="pg-eyebrow">Morada</p>
                            <p>Rua do Porto, 94 · 4590-196 Figueiró</p>
                            <hr class="pg-rule"/>
                            <p class="pg-eyebrow mt-4">Telefone</p>
                            <p><a href="tel:+351255181731">+351 255 181 731</a> · <a href="tel:+351917196677">+351 917 196 677</a></p>
                            <hr class="pg-rule"/>
                            <p class="pg-eyebrow mt-4">Email</p>
                            <p><a href="mailto:lusosofa@gmail.com">lusosofa@gmail.com</a></p>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    </t>
</t>"""

ESPANHOL = {
    "Estofos desde 2016 · Figueiró": "Tapicería desde 2016 · Figueiró",
    "Feito à medida do seu espaço": "Hecho a la medida de su espacio",
    "Uma oficina artesanal que cresceu, e continua a dar forma às ideias de quem desenha.":
        "Un taller artesanal que creció, y que sigue dando forma a las ideas de quien diseña.",
    "Ver o catálogo": "Ver el catálogo",
    "Trabalho à medida": "Trabajo a medida",
    "O que fazemos": "Lo que hacemos",
    "Sofás, cadeirões e quarto": "Sofás, sillones y dormitorio",
    "Ver os 12 artigos": "Ver los 12 artículos",
    "Sofás e chaise longues": "Sofás y chaise longues",
    "Cadeirões": "Sillones",
    "Quarto": "Dormitorio",
    "Coleção Traços": "Colección Traços",
    "Cada peça começa num traço": "Cada pieza empieza en un trazo",
    "A Coleção Traços vem demonstrar toda a versatilidade e elegância de uma linha criada a pensar em si. O conforto aliado a um design moderno e cativante vão poder fazer parte da sua casa.":
        "La Colección Traços demuestra toda la versatilidad y elegancia de una línea creada pensando en usted. El confort unido a un diseño moderno y cautivador podrán formar parte de su hogar.",
    "Deixe que o nosso traço embeleze o seu espaço.":
        "Deje que nuestro trazo embellezca su espacio.",
    "A nossa história": "Nuestra historia",
    "Especialidade": "Especialidad",
    "Capitoné": "Capitoné",
    "Versátil, elegante e sofisticado, cruza o clássico e o moderno e dá vida a qualquer produto.":
        "Versátil, elegante y sofisticado, cruza lo clásico y lo moderno y da vida a cualquier producto.",
    "Trabalho por encomenda": "Trabajo por encargo",
    "Fale connosco": "Hable con nosotros",
    "Tem um projeto em mãos?": "¿Tiene un proyecto entre manos?",
    "Diga-nos o que precisa e respondemos com uma proposta.":
        "Díganos lo que necesita y le respondemos con una propuesta.",
    "Pedir orçamento": "Pedir presupuesto",
    "Morada": "Dirección",
    "Telefone": "Teléfono",
}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true", help="escreve mesmo")
    ap.add_argument("--creds", default=os.path.expanduser("~/.lusosofa_odoo.json"))
    args = ap.parse_args()

    odoo = Odoo(json.load(open(args.creds, encoding="utf-8")))
    modo = "APLICAR" if args.aplicar else "dry-run (não escreve nada)"
    print(f"\nNova página inicial [{modo}]")
    print(f"{odoo.url} · base {odoo.db}\n")

    xml.dom.minidom.parseString(CORPO.replace("t-call=", "data-t-call=")
                                     .replace("t-set=", "data-t-set=")
                                     .replace("t-value=", "data-t-value="))
    print(f"  conteúdo novo: {len(CORPO)} caracteres, XML válido")

    for chave, url in IMG.items():
        pid = int(url.rsplit("/", 1)[1])
        att = odoo.search_read("ir.attachment", [["id", "=", pid], ["public", "=", True]], ["name"])
        if not att:
            raise SystemExit(f"ABORTADO: a imagem {url} não existe ou não é pública.")
        print(f"  {chave:8} {url:18} {att[0]['name']}")

    vistas = odoo.kw("ir.ui.view", "search_read",
                     [[["key", "=", CHAVE], ["website_id", "!=", False]]],
                     {"fields": ["id"], "context": {"active_test": False}})
    if len(vistas) != 1:
        raise SystemExit(f"ABORTADO: esperava uma cópia de {CHAVE}, achei {len(vistas)}.")
    vid = vistas[0]["id"]
    antes = odoo.kw("ir.ui.view", "read", [[vid], ["arch_db"]],
                    {"context": {"lang": "en_US"}})[0]["arch_db"]
    print(f"\n  vista {vid}: {len(antes)} -> {len(CORPO)} caracteres")
    print(f"  saem: a colagem de imagens e a secção «A Nossa Seleção» "
          f"(modelos Noa, Porto e Estoril deixam de aparecer no site)")

    if not args.aplicar:
        print("\n  Nada foi escrito. Para aplicar: --aplicar\n")
        return

    carimbo = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    destino = RAIZ / f".backup_lusosofa_homepage_{carimbo}.json"
    destino.write_text(json.dumps({
        "tirado_em_utc": carimbo, "base": odoo.db, "url": odoo.url,
        "accao": "reescrever a página inicial (estrutura aprovada 2026-09-28)",
        "vista": vid, "arch_db_antes": antes,
        "traducoes_antes": odoo.kw("ir.ui.view", "get_field_translations",
                                   [[vid], "arch_db"])[0],
        "como_reverter": f"ir.ui.view write [[{vid}], {{'arch_db': <arch_db_antes>}}] com lang en_US",
    }, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"\n  resguardo: {destino.name}")

    odoo.kw("ir.ui.view", "write", [[vid], {"arch_db": CORPO}], {"context": {"lang": "en_US"}})
    print("  página inicial reescrita")

    odoo.kw("ir.ui.view", "update_field_translations", [[vid], "arch_db", {"es_ES": ESPANHOL}])
    print(f"  {len(ESPANHOL)} termos traduzidos para espanhol")

    print("\nverificação — contra as páginas servidas")
    ok = True
    pt = urllib.request.urlopen(odoo.url + "/", timeout=90).read().decode("utf-8", "replace")
    es = urllib.request.urlopen(odoo.url + "/es", timeout=90).read().decode("utf-8", "replace")

    for texto in ["Feito à medida do seu espaço", "Cada peça começa num traço",
                  "Tem um projeto em mãos?", "Pedir orçamento"]:
        print(f"  / tem {texto!r}: {'sim' if texto in pt else 'NÃO'}")
        ok = ok and texto in pt
    for texto in ["Hecho a la medida de su espacio", "Cada pieza empieza en un trazo",
                  "Pedir presupuesto"]:
        print(f"  /es tem {texto!r}: {'sim' if texto in es else 'NÃO'}")
        ok = ok and texto in es

    imagens = len([u for u in set(IMG.values()) if u in pt])
    print(f"  imagens da nova página presentes: {imagens}/{len(set(IMG.values()))}")
    ok = ok and imagens == len(set(IMG.values()))

    # As ligações das três categorias têm de responder.
    for u in ["/shop/category/sofas-e-chaise-longues-1", "/shop/category/cadeiroes-2",
              "/shop/category/quarto-3", "/shop", "/projetos", "/about-us", "/contactus"]:
        cod = urllib.request.urlopen(odoo.url + u, timeout=60).status
        if cod != 200:
            print(f"  ! {u}: HTTP {cod}")
            ok = False
    print(f"  as 7 ligações da página respondem 200: {'sim' if ok else 'NÃO'}")

    print("\n" + ("Página inicial no ar." if ok else
                  "ATENÇÃO: algo não confere. Vê o resguardo."))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
