#!/usr/bin/env python3
"""Traduz para espanhol o conteúdo próprio do website da LusoSofá.

Por defeito faz **dry-run**. Para escrever mesmo:

    python3 scripts_lusosofa/traduzir_espanhol.py --aplicar

O que este script traduz é só o que é **da LusoSofá**: os nomes dos menus e
das categorias criados por nós, e o texto das duas páginas escritas à mão. A
interface do Odoo já vem traduzida com o idioma e não se toca.

Dois mecanismos, porque os campos são de naturezas diferentes:

* ``website.menu.name`` e ``product.public.category.name`` são campos de texto
  traduzidos por registo — escreve-se com ``lang`` no contexto;
* ``ir.ui.view.arch_db`` é traduzido **por termo** (``xml_translate``), e cada
  termo é um bloco de HTML, não texto simples. Escrever o documento inteiro
  substituiria a estrutura; o caminho certo é ``update_field_translations``,
  que casa termo a termo e deixa a marcação intacta.

A marcação dos termos é copiada **tal e qual** da origem — só muda o texto lá
dentro. Se um termo de origem deixar de existir (porque alguém editou a página
no editor do site), o script diz qual e não escreve nada: uma tradução que
falha o casamento fica pendurada sem nada a apontar-lhe.
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

LINGUA = "es_ES"

# --- menus e categorias -------------------------------------------------------
# Os menus repetem-se em duas árvores; só interessa a que o site serve.
ARVORE_EM_USO = "Top Menu for Website 1"

MENUS = {
    "Início": "Inicio",
    "Produtos": "Productos",
    "História": "Historia",
    "Contacte-nos": "Contáctenos",
}

CATEGORIAS = {
    "Sofás e chaise longues": "Sofás y chaise longues",
    "Cadeirões": "Sillones",
    "Quarto": "Dormitorio",
}

# --- páginas ------------------------------------------------------------------
# Chave: termo de origem, exactamente como o Odoo o guarda, marcação incluída.

HOMEPAGE = {
    '<i class="fa fa-fw fa-building-o" role="presentation"/>\n                        Office':
        '<i class="fa fa-fw fa-building-o" role="presentation"/>\n                        Oficina',
    '<i class="fa fa-fw fa-envelope-o" role="presentation"/>\n                        Email':
        '<i class="fa fa-fw fa-envelope-o" role="presentation"/>\n                        Correo electrónico',
    '<i class="fa fa-fw fa-phone" role="presentation"/>\n                        Phone':
        '<i class="fa fa-fw fa-phone" role="presentation"/>\n                        Teléfono',
    '<span class="carousel-control-next-icon" aria-hidden="true"/>\n                <span class="visually-hidden o_default_snippet_text">Next</span>':
        '<span class="carousel-control-next-icon" aria-hidden="true"/>\n                <span class="visually-hidden o_default_snippet_text">Siguiente</span>',
    '<span class="carousel-control-prev-icon" aria-hidden="true"/>\n                <span class="visually-hidden o_default_snippet_text">Previous</span>':
        '<span class="carousel-control-prev-icon" aria-hidden="true"/>\n                <span class="visually-hidden o_default_snippet_text">Anterior</span>',
    '<span class="h1-fs">A Nossa Seleção</span>':
        '<span class="h1-fs">Nuestra Selección</span>',
    '<span>A coleção traços, desenvolvida pela empresa LusoSofá, vem demonstrar toda a versatilidade e elegância de uma linha criada a pensar em si.</span>':
        '<span>La colección Traços, desarrollada por LusoSofá, demuestra toda la versatilidad y elegancia de una línea creada pensando en usted.</span>',
    '<span>Deixe que o nosso traço embeleze o seu espaço.</span>':
        '<span>Deje que nuestro trazo embellezca su espacio.</span>',
    '<span>O conforto aliado a um design moderno e cativante vão poder fazer parte da sua casa.</span>':
        '<span>El confort unido a un diseño moderno y cautivador podrá formar parte de su hogar.</span>',
    '<span style="font-size: 2.625rem;">Contacte-nos</span>':
        '<span style="font-size: 2.625rem;">Contáctenos</span>',
    '<span style="font-weight: normal;">&amp;nbsp;Coleção Traços</span>':
        '<span style="font-weight: normal;">&amp;nbsp;Colección Traços</span>',
    'Carousel indicator': 'Indicador del carrusel',
    'Descubra mais': 'Descubra más',
    'Link to product': 'Enlace al producto',
    'Próximo': 'Siguiente',
}

SOBRE_NOS = {
    'Sobre nós': 'Sobre nosotros',
    '<span>A LusoSofá\nsurge no mercado em 2016, inspirada pelo desejo de criar autenticidade e\nproporcionar conforto, tornando-se especializada na conceção de estofos.</span>':
        '<span>LusoSofá surge en el mercado en 2016, inspirada por el deseo de crear autenticidad y proporcionar confort, especializándose en el diseño de tapicería.</span>',
    '<span>A pequena\noficina artesanal cresceu rapidamente e, a partir de 2021, tornou-se mais\nindustrializada em carácter e dimensão, de forma a corresponder com as\nnecessidades dos diferentes mercados. </span>':
        '<span>El pequeño taller artesanal creció rápidamente y, a partir de 2021, se industrializó en carácter y dimensión, para responder a las necesidades de los distintos mercados. </span>',
    '<span>A empresa é\nconstituída por uma equipa com vastos conhecimentos em diversas áreas, sendo\nque, uma das áreas que temos mais destaque é na fabricação de Capitoné.</span>':
        '<span>La empresa está formada por un equipo con amplios conocimientos en diversas áreas, siendo la fabricación de capitoné una de aquellas en las que más destacamos.</span>',
    '<span>Uma forma de estofo\nque é intemporal e complementa muito bem uma infinidade de ambientes.</span>':
        '<span>Una forma de tapizado atemporal, que complementa muy bien una infinidad de ambientes.</span>',
    '<span>O principal\nobjetivo é a satisfação do cliente, além disso, somos guiados pelo nosso\ncompromisso de alcançar a excelência em tudo o que fazemos.</span>':
        '<span>El principal objetivo es la satisfacción del cliente; además, nos guía el compromiso de alcanzar la excelencia en todo lo que hacemos.</span>',
    '<span>A LusoSofá dá\nforma às ideias e projetos dos designers, canalizando as suas energias\ncriativas baseadas em diferentes raízes culturais, no desenvolvimento de produtos\npara indoor e outdoor para os segmentos residencial e Hotelaria. Esses produtos\nrefletem a identidade LusoSofá, bem como a evolução dos hábitos de vida.</span>':
        '<span>LusoSofá da forma a las ideas y proyectos de los diseñadores, canalizando sus energías creativas, nacidas de distintas raíces culturales, en el desarrollo de productos de interior y exterior para los segmentos residencial y de hostelería. Estos productos reflejan la identidad LusoSofá, así como la evolución de los hábitos de vida.</span>',
    '<span>Contacte-nos\npara o restauro de qualquer tipo de produto, se tem uma peça de grande valor\nsentimental, nós realizamos o seu restauro e damos-lhe uma vida nova, de\nelegância e bom gosto!</span>':
        '<span>Contáctenos para la restauración de cualquier tipo de producto. Si tiene una pieza de gran valor sentimental, la restauramos y le damos una vida nueva, de elegancia y buen gusto.</span>',
    '<span>Especialistas\nem capitonê</span>':
        '<span>Especialistas en capitoné</span>',
    '<span>Realizar\ntrabalhos em capitonê é uma arte! O capitonê está de volta, versátil, elegante\ne sofisticado, cruza o clássico e o moderno e dá vida a qualquer produto.</span>':
        '<span>¡Realizar trabajos en capitoné es un arte! El capitoné está de vuelta: versátil, elegante y sofisticado, cruza lo clásico y lo moderno y da vida a cualquier producto.</span>',
}

# --- rodapé -------------------------------------------------------------------
# O rodapé é a parte do site que aparece em todas as páginas, e por isso é a
# que se nota menos estar por traduzir: a 2026-09-26 saía inteiramente em
# português no /es, dias depois de o resto estar feito. É o preço de traduzir
# página a página — o que é comum a todas fica de fora da lista de todas.
#
# Sem tradução, de propósito: a morada (não se traduzem moradas), o email, os
# números de telefone e «LusoSofá», que é marca.

RODAPE = {
    '<span style="font-size: 1.5rem;"><font style="color: rgb(189, 148, 0);">Serviços</font></span>':
        '<span style="font-size: 1.5rem;"><font style="color: rgb(189, 148, 0);">Servicios</font></span>',
    '<span style="font-size: 1.5rem;"><font style="color: rgb(189, 148, 0);">Siga-nos</font></span>':
        '<span style="font-size: 1.5rem;"><font style="color: rgb(189, 148, 0);">Síganos</font></span>',
    '<span style="font-size: 1.5rem;"><font style="color: rgb(189, 148, 0);">Fale connosco</font></span>':
        '<span style="font-size: 1.5rem;"><font style="color: rgb(189, 148, 0);">Hable con nosotros</font></span>',
    '<font class="text-o-color-3">Início</font>': '<font class="text-o-color-3">Inicio</font>',
    '<font class="text-o-color-3">História</font>': '<font class="text-o-color-3">Historia</font>',
    '<font class="text-o-color-3">Projetos</font>': '<font class="text-o-color-3">Proyectos</font>',
    '<font class="text-o-color-3">Produtos</font>': '<font class="text-o-color-3">Productos</font>',
    '(Chamada para a rede fixa nacional)': '(Llamada a la red fija nacional)',
    '(Chamada para a rede móvel nacional)': '(Llamada a la red móvil nacional)',
}

PAGINAS = [("/", HOMEPAGE), ("/about-us", SOBRE_NOS)]
VISTA_RODAPE = "website.template_footer_links"

# --- correcções ao português --------------------------------------------------
# A secção de contactos da homepage ficou com rótulos em inglês, herdados do
# tema. Corrigem-se como tradução pt_PT dos mesmos termos, sem tocar na origem:
# assim ficam reversíveis apagando o valor, e o termo de origem continua a ser a
# chave que o espanhol também usa.
#
# «Email» fica como está, de propósito. É empréstimo naturalizado em português e
# não é um rótulo por traduzir — mudá-lo seria mexer por mexer.

CORRECOES_PT = {
    "/": {
        '<i class="fa fa-fw fa-building-o" role="presentation"/>\n                        Office':
            '<i class="fa fa-fw fa-building-o" role="presentation"/>\n                        Escritório',
        '<i class="fa fa-fw fa-phone" role="presentation"/>\n                        Phone':
            '<i class="fa fa-fw fa-phone" role="presentation"/>\n                        Telefone',
    },
}


def vista_da_pagina(odoo, url):
    pags = [p for p in odoo.search_read("website.page", [["url", "=", url]],
                                        ["id", "view_id", "is_published"])
            if p["is_published"] and p["view_id"]]
    if not pags:
        raise SystemExit(f"ABORTADO: não encontrei página publicada em {url}")
    # A página vazia duplicada não tem termos; fica-se pela que tem conteúdo.
    melhor, mais = None, -1
    for p in pags:
        n = len({t["source"] for t in odoo.kw("ir.ui.view", "get_field_translations",
                                              [[p["view_id"][0]], "arch_db"])[0]})
        if n > mais:
            melhor, mais = p, n
    return melhor["view_id"][0]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true", help="escreve mesmo")
    ap.add_argument("--creds", default=os.path.expanduser("~/.lusosofa_odoo.json"))
    args = ap.parse_args()

    odoo = Odoo(json.load(open(args.creds, encoding="utf-8")))
    modo = "APLICAR" if args.aplicar else "dry-run (não escreve nada)"
    print(f"\nTradução para espanhol [{modo}]")
    print(f"{odoo.url} · base {odoo.db}\n")

    if not odoo.search_read("res.lang", [["code", "=", LINGUA], ["active", "=", True]], ["id"]):
        raise SystemExit(f"ABORTADO: {LINGUA} não está activo nesta base.")

    plano = {"menus": [], "categorias": [], "paginas": {}}
    faltas = []

    arvore = odoo.search_read("website.menu", [["name", "=", ARVORE_EM_USO]], ["id"])
    if not arvore:
        raise SystemExit(f"ABORTADO: não encontrei a árvore de menus {ARVORE_EM_USO!r}.")
    for m in odoo.search_read("website.menu", [["parent_id", "=", arvore[0]["id"]]],
                              ["id", "name"]):
        if m["name"] in MENUS:
            plano["menus"].append((m["id"], m["name"], MENUS[m["name"]]))
        else:
            faltas.append(f"menu {m['name']!r} sem tradução definida")

    for c in odoo.search_read("product.public.category", [], ["id", "name"]):
        if c["name"] in CATEGORIAS:
            plano["categorias"].append((c["id"], c["name"], CATEGORIAS[c["name"]]))
        else:
            faltas.append(f"categoria {c['name']!r} sem tradução definida")

    for url, mapa in PAGINAS:
        vista = vista_da_pagina(odoo, url)
        existentes = {t["source"] for t in
                      odoo.kw("ir.ui.view", "get_field_translations", [[vista], "arch_db"])[0]}
        perdidos = [s for s in mapa if s not in existentes]
        if perdidos:
            for s in perdidos:
                faltas.append(f"{url}: termo já não existe na página — {s[:70]!r}")
        plano["paginas"][url] = (vista, {s: v for s, v in mapa.items() if s in existentes})

    print("  menus")
    for _, pt, es in plano["menus"]:
        print(f"     {pt:26} -> {es}")
    print("\n  categorias")
    for _, pt, es in plano["categorias"]:
        print(f"     {pt:26} -> {es}")
    for url, (vista, mapa) in plano["paginas"].items():
        print(f"\n  {url}  (vista {vista}) — {len(mapa)} termos")

    rod = odoo.kw("ir.ui.view", "search_read",
                  [[["key", "=", VISTA_RODAPE], ["website_id", "!=", False]]],
                  {"fields": ["id"], "context": {"active_test": False}})
    if len(rod) != 1:
        raise SystemExit(f"ABORTADO: esperava uma cópia de {VISTA_RODAPE}, achei {len(rod)}.")
    rod_id = rod[0]["id"]
    existentes_rod = {t["source"] for t in
                      odoo.kw("ir.ui.view", "get_field_translations", [[rod_id], "arch_db"])[0]}
    perdidos_rod = [s for s in RODAPE if s not in existentes_rod]
    for s in perdidos_rod:
        faltas.append(f"rodapé: termo já não existe — {s[:70]!r}")
    plano["rodape"] = (rod_id, {s: v for s, v in RODAPE.items() if s in existentes_rod})
    print(f"\n  rodapé (vista {rod_id}) — {len(plano['rodape'][1])} termos")

    plano["correcoes_pt"] = {}
    for url, mapa in CORRECOES_PT.items():
        vista = plano["paginas"][url][0]
        existentes = {t["source"] for t in
                      odoo.kw("ir.ui.view", "get_field_translations", [[vista], "arch_db"])[0]}
        em_falta = [s for s in mapa if s not in existentes]
        for s in em_falta:
            faltas.append(f"{url} (pt): termo já não existe — {s[:70]!r}")
        plano["correcoes_pt"][url] = (vista, {s: v for s, v in mapa.items() if s in existentes})
        print(f"\n  correcções ao português em {url} — {len(plano['correcoes_pt'][url][1])}")
        for s, v in plano["correcoes_pt"][url][1].items():
            print(f"     {s.rsplit('>', 1)[-1].strip()!r} -> {v.rsplit('>', 1)[-1].strip()!r}")

    if faltas:
        print("\n  avisos:")
        for f in faltas:
            print(f"     ! {f}")
        if any("já não existe" in f for f in faltas):
            raise SystemExit(
                "\nABORTADO: há termos de origem que já não existem na página. "
                "Alguém a editou depois de este script ser escrito — actualiza as "
                "traduções antes de escrever, senão ficam penduradas sem efeito."
            )

    if not args.aplicar:
        print("\n  Nada foi escrito. Para aplicar: --aplicar\n")
        return

    carimbo = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    destino = RAIZ / f".backup_lusosofa_traducao_{carimbo}.json"
    destino.write_text(json.dumps({
        "tirado_em_utc": carimbo, "base": odoo.db, "url": odoo.url,
        "accao": f"traduzir conteudo proprio para {LINGUA}",
        "traducoes_antes": {
            url: odoo.kw("ir.ui.view", "get_field_translations", [[v], "arch_db"])[0]
            for url, (v, _) in plano["paginas"].items()
        },
        "como_reverter": ("update_field_translations com value vazio em cada termo, "
                          "e reescrever os nomes de menu/categoria em es_ES"),
    }, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"\n  resguardo: {destino.name}")

    for mid, pt, es in plano["menus"]:
        odoo.kw("website.menu", "write", [[mid], {"name": es}], {"context": {"lang": LINGUA}})
        print(f"  menu: {pt} -> {es}")
    for cid, pt, es in plano["categorias"]:
        odoo.kw("product.public.category", "write", [[cid], {"name": es}],
                {"context": {"lang": LINGUA}})
        print(f"  categoria: {pt} -> {es}")
    for url, (vista, mapa) in plano["paginas"].items():
        odoo.kw("ir.ui.view", "update_field_translations", [[vista], "arch_db", {LINGUA: mapa}])
        print(f"  {url}: {len(mapa)} termos escritos em {LINGUA}")
    rod_id, rod_mapa = plano["rodape"]
    if rod_mapa:
        odoo.kw("ir.ui.view", "update_field_translations",
                [[rod_id], "arch_db", {LINGUA: rod_mapa}])
        print(f"  rodapé: {len(rod_mapa)} termos escritos em {LINGUA}")
    for url, (vista, mapa) in plano["correcoes_pt"].items():
        if mapa:
            odoo.kw("ir.ui.view", "update_field_translations",
                    [[vista], "arch_db", {"pt_PT": mapa}])
            print(f"  {url}: {len(mapa)} rótulos corrigidos em pt_PT")

    print("\nverificação")
    ok = True
    for mid, pt, es in plano["menus"]:
        lido = odoo.kw("website.menu", "read", [[mid], ["name"]],
                       {"context": {"lang": LINGUA}})[0]["name"]
        if lido != es:
            print(f"  ! menu {pt}: ficou {lido!r}, esperava {es!r}")
            ok = False
    for url, (vista, mapa) in plano["paginas"].items():
        posto = {t["source"]: t["value"] for t in
                 odoo.kw("ir.ui.view", "get_field_translations", [[vista], "arch_db"])[0]
                 if t["lang"] == LINGUA}
        maus = [s for s, v in mapa.items() if posto.get(s) != v]
        print(f"  {url}: {len(mapa) - len(maus)}/{len(mapa)} termos conferem")
        ok = ok and not maus

    # O que conta é a página que o visitante recebe, não o que a base diz.
    pagina = urllib.request.urlopen(odoo.url + "/es", timeout=90).read().decode("utf-8", "replace")
    for esperado in ["Inicio", "Productos", "Historia", "Contáctenos"]:
        visivel = f">{esperado}<" in pagina or f">{esperado} " in pagina
        print(f"  /es mostra {esperado!r}: {'sim' if visivel else 'NÃO'}")
        ok = ok and visivel

    # O rodapé aparece em todas as páginas, e é o que menos se nota por
    # traduzir. Verifica-se no corpo do rodapé servido, não na base.
    rodape_es = re.search(r"<footer.*?</footer>", pagina, re.S)
    corpo_rod = rodape_es.group(0) if rodape_es else pagina
    for esperado in ["Servicios", "Síganos", "Hable con nosotros", "Proyectos", "Productos"]:
        visivel = esperado in corpo_rod
        print(f"  rodapé /es mostra {esperado!r}: {'sim' if visivel else 'NÃO'}")
        ok = ok and visivel
    for indesejado in ["Serviços", "Siga-nos", "Fale connosco"]:
        limpo = indesejado not in corpo_rod
        print(f"  rodapé /es já não mostra {indesejado!r}: {'sim' if limpo else 'NÃO'}")
        ok = ok and limpo

    pt = urllib.request.urlopen(odoo.url + "/", timeout=90).read().decode("utf-8", "replace")
    for esperado in ["Escritório", "Telefone"]:
        print(f"  / mostra {esperado!r}: {'sim' if esperado in pt else 'NÃO'}")
        ok = ok and esperado in pt
    for indesejado in ["Office", "Phone"]:
        limpo = indesejado not in pt
        print(f"  / já não mostra {indesejado!r}: {'sim' if limpo else 'NÃO'}")
        ok = ok and limpo

    print("\n" + ("Traduzido." if ok else "ATENÇÃO: alguma coisa não confere. Vê o resguardo."))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
