#!/usr/bin/env python3
"""Fecha o português que ficou por traduzir na versão espanhola.

Por defeito faz **dry-run**. Para escrever mesmo:

    python3 scripts_lusosofa/espanhol_em_falta.py --aplicar

## Porquê existe um segundo script de espanhol

O `traduzir_espanhol.py` correu a 2026-09-24 e deixou o site traduzido. Só que
**a página inicial foi reescrita a 26 e a página `/projetos` nasceu a 25** —
depois da passagem. Conteúdo criado a seguir a uma tradução não fica traduzido,
e nada avisa: a versão espanhola continua a responder 200 e a parecer inteira.

A lição não é sobre as sequências que este script corrige. É que **traduzir não
é um passo que se dá uma vez**: cada página nova reabre a dívida.

## Como isto foi encontrado, e porque interessa

`FACTO OBSERVADO` (2026-09-28): a primeira varredura procurou uma lista curta de
palavras portuguesas e devolveu três nomes de produto — «Cadeirão Oslo» e os
dois «Cadeirão ... Giratório». Parecia um descuido pequeno.

Era o contrário. Os três só apareceram **por terem `ã`**. Ao ir ver produto a
produto, **nenhum dos doze nomes estava traduzido**: «Cabeceira Moly», «Cama
Sally» e «Chaiselong Kenedy» tinham passado ao lado do detector por não terem
ortografia que o espanhol não use. A loja espanhola estava inteira em português
e a medição dizia que faltavam três palavras.

Daí a verificação no fim ter duas partes, e não uma:

* uma **varredura por ortografia** (`ã`, `õ`, `-ção`, `-ões`) e por vocabulário
  de mobiliário, que apanha texto corrido esquecido;
* uma **verificação nome a nome** de todos os produtos publicados, que não
  procura sinais nenhuns — exige que cada nome tenha tradução espanhola ou
  esteja na lista dos que são iguais de propósito, com a razão escrita.

A segunda existe porque a primeira falhou. Um detector que procura sinais só
encontra o que tem sinais, e é por isso que sozinho dá falsa segurança.

## O que fica deliberadamente por mudar

**Os nomes de modelo.** Traduz-se o substantivo que diz o que a peça é —
«Cadeirão» para «Sillón», «Cabeceira» para «Cabecero» —, e o resto fica como a
oficina lhe chama. Inventar «Cuadros Capitoné» para «Quadrados Puxados» seria
criar um nome de produto que não existe em lado nenhum.

**As duas Chaiselong**, porque a grafia de «Chaiselong» e «Kenedy» está em
aberto com a cliente e não se corrige duas vezes a mesma palavra.

**As ligações «Projeto 70484» e «Projeto 71172»** no rodapé, que apontam para os
PDF de financiamento público. Ficam em português nas duas versões do site —
**decisão do João Barros, 2026-09-28**, perguntada e respondida. São referências
a programas de financiamento portugueses, identificados pela sua designação
portuguesa, e os próprios PDF estão em português: traduzir o rótulo faria a
ligação prometer um documento espanhol que não existe.

Isto não é o mesmo caso que o resto deste ficheiro. Tudo o mais aqui era
esquecimento; isto é escolha, e está escrito para que a próxima varredura não a
volte a levantar como defeito.
"""

import argparse
import datetime
import html
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aplicar_identidade import Odoo, RAIZ  # noqa: E402

LINGUA = "es_ES"

# Rótulo de menu. Um registo só, que serve as cinco páginas.
MENUS = {"/projetos": ("Projetos", "Proyectos")}

# Traduções por página, indexadas pelo **texto português** e não pela
# sequência-fonte. A razão está na secção de cima: o Odoo indexa o termo com a
# marcação à volta — `<span class="pg-eyebrow">O que fazemos</span>` —, e
# transcrever essa marcação à mão é como se falha. O script localiza a
# sequência-fonte que contém o texto e substitui só o texto lá dentro.
PAGINAS_TERMOS = {
    "/": {
        "Coleção Traços": "Colección Traços",
        "Especialidade": "Especialidad",
        "Estofos desde 2016 · Figueiró": "Tapicería desde 2016 · Figueiró",
        "Fale connosco": "Hable con nosotros",
        "O que fazemos": "Lo que hacemos",
        "Email": "Correo electrónico",
        "Cabeceira em capitoné verde-petróleo, com botão puxado em losangos":
            "Cabecero en capitoné verde petróleo, con botón capitoneado en rombos",
        "Desenho a lápis de um sofá, assinado Alcântara":
            "Dibujo a lápiz de un sofá, firmado Alcântara",
        "Par de cadeirões de braços arredondados em tecido terracota":
            "Pareja de sillones de brazos redondeados en tejido terracota",
        "Quarto com cama de cabeceira alta em capitoné":
            "Dormitorio con cama de cabecero alto en capitoné",
        "Sala ampla com sofá modular claro": "Salón amplio con sofá modular claro",
        "Sofá seccional numa sala ampla com arco":
            "Sofá seccional en un salón amplio con arco",
    },
    "/about-us": {
        "A nossa história": "Nuestra historia",
        "Desenho a lápis de um sofá, assinado Alcântara":
            "Dibujo a lápiz de un sofá, firmado Alcântara",
        "Quarto com cama de cabeceira alta em capitoné e laterais em aba":
            "Dormitorio con cama de cabecero alto en capitoné y laterales en ala",
        "Sofá de canto em tecido azul-marinho, com apoios de cabeça e pés metálicos":
            "Sofá rinconera en tejido azul marino, con reposacabezas y patas metálicas",
        "Sofá em veludo verde-esmeralda, com pés em madeira clara":
            "Sofá en terciopelo verde esmeralda, con patas de madera clara",
        "Sofá modular claro numa sala ampla, com lustre de cristal":
            "Sofá modular claro en un salón amplio, con lámpara de cristal",
    },
    "/contactus": {
        "Contacte-nos": "Contáctenos",
        "Nome": "Nombre",
        "Mensagem": "Mensaje",
        "Questão": "Pregunta",
        "Submeter": "Enviar",
        "(Chamada para a rede fixa nacional)": "(Llamada a la red fija nacional)",
        "(Chamada para a rede móvel nacional)": "(Llamada a la red móvil nacional)",
    },
    "/projetos": {
        "Trabalho por encomenda": "Trabajo por encargo",
        "Cadeirão em bouclé com estrutura em madeira, fotografado no showroom":
            "Sillón en bouclé con estructura de madera, fotografiado en el showroom",
        "Cadeirão em tecido bouclé claro com estrutura em madeira maciça":
            "Sillón en tejido bouclé claro con estructura de madera maciza",
        "Par de cadeirões de braços arredondados em tecido terracota":
            "Pareja de sillones de brazos redondeados en tejido terracota",
        "Quarto com cabeceira estofada e cadeirão de braços arredondados":
            "Dormitorio con cabecero tapizado y sillón de brazos redondeados",
        "Sofá de encosto canelado em tecido claro, com pés metálicos dourados":
            "Sofá de respaldo acanalado en tejido claro, con patas metálicas doradas",
        "Sofá modular de linhas curvas numa sala ampla com luz natural":
            "Sofá modular de líneas curvas en un salón amplio con luz natural",
        "Sofá seccional com chaise longue em tecido cinzento texturado":
            "Sofá seccional con chaise longue en tejido gris texturizado",
    },
}

# Sequências que se escrevem igual nas duas línguas. Ficam declaradas para a
# verificação as aceitar sem as reescrever — e para a decisão ficar visível.
IGUAIS_NAS_VISTAS = {"Capitoné", "Contacto", "Empresa", "LusoSofá", "Morada",
                     "Telefone", "Quarto", "Sobre nós"}

# Só o substantivo que diz o que a peça é. Ver o cabeçalho.
PRODUTOS = {
    "Cadeirão Emily Giratório": "Sillón Emily Giratorio",
    "Cadeirão Sofy Giratório": "Sillón Sofy Giratorio",
    "Cadeirão Oslo": "Sillón Oslo",
    "Cabeceira Capitoné": "Cabecero Capitoné",
    "Cabeceira Moly": "Cabecero Moly",
    "Cabeceira Ouros": "Cabecero Ouros",
    "Cabeceira Quadrados Puxados": "Cabecero Quadrados Puxados",
}

# Nomes que ficam iguais nas duas línguas, e porquê. A verificação exige que
# todo o produto publicado esteja traduzido **ou** apareça aqui — é o que
# impede um nome esquecido de passar por decisão.
IGUAIS_DE_PROPOSITO = {
    "Cama Sally": "«cama» escreve-se igual em espanhol",
    "Bali Modular": "«modular» escreve-se igual; Bali é nome próprio",
    "Sofá Sweet": "«sofá» escreve-se igual em espanhol",
    "Chaiselong Kenedy": "grafia em aberto com a cliente — não se mexe duas vezes",
    "Chaiselong Singapura": "grafia em aberto com a cliente — não se mexe duas vezes",
}

PAGINAS_ES = ["/es", "/es/shop", "/es/about-us", "/es/projetos", "/es/contactus"]

# Ortografia que o espanhol não tem, mais o vocabulário de mobiliário que a
# primeira varredura não trazia e que foi o que a deixou passar a loja inteira.
SINAIS = re.compile(
    r"[ãõ]|\bnão\b|\bmuito\b|\bfazemos\b|\bnossa?\b|\bnossos?\b|\bpeças?\b|"
    r"\bartigos\b|\bcoleç|\bprojetos?\b|\bhistória\b|\bcontacte\b|\bconnosco\b|"
    r"\bsaber mais\b|\bà medida\b|\bquestão\b|\bmensagem\b|\bnome\b|"
    r"\bcadeirão\b|\bcadeirões\b|\bcabeceiras?\b|\bpuxados?\b|\bgiratório\b|"
    r"\bestofos?\b|\bsob consulta\b|\bver o\b",
    re.I,
)

# O que a varredura acusa e é decisão, não esquecimento. Sem esta lista a
# verificação falhava para sempre sobre coisas já decididas — e uma verificação
# que falha sempre é uma verificação que se deixa de ler.
#
#   `Projeto NNNNN` .......... os PDF de financiamento no rodapé, que ficam em
#                              português por decisão de 2026-09-28 (ver cabeçalho)
#   `Quadrados Puxados` ...... nome de modelo, mantido de propósito
TOLERADO = re.compile(r"^Projeto \d+$|Quadrados Puxados")


def texto_visivel(pagina):
    corpo = re.sub(r"(?s)<(script|style|head)\b.*?</\1>", " ", pagina)
    return [l.strip() for l in
            html.unescape(re.sub(r"<[^>]+>", "\n", corpo)).split("\n") if l.strip()]


def varrer(url_base):
    """Devolve {página: [linhas suspeitas]} na versão espanhola do site."""
    achados = {}
    for pag in PAGINAS_ES:
        h = urllib.request.urlopen(url_base + pag, timeout=90).read().decode("utf-8", "replace")
        suspeitas = sorted({l for l in texto_visivel(h)
                            if SINAIS.search(l) and not TOLERADO.search(l)})
        if suspeitas:
            achados[pag] = suspeitas
    return achados


def mapa_de_termos(odoo, vista, textos):
    """Converte {texto português: espanhol} em {sequência-fonte: valor}.

    Duas regras, e ambas custaram uma passagem falhada para aparecer:

    * a chave que o Odoo indexa traz a marcação à volta, por isso procura-se o
      texto **dentro** de cada sequência-fonte em vez de o dar como chave;
    * só se toca em sequências que **ainda não têm espanhol**. Sem isto, o
      texto «Coleção Traços» — que também aparece a meio de um parágrafo já
      traduzido — reescrevia esse parágrafo com português pelo meio.

    Devolve ``(mapa, nao_encontrados)``. Um texto que não case com nenhuma
    sequência é erro: quer dizer que a página mudou e a tradução é para outra
    coisa qualquer.
    """
    traducoes = odoo.kw("ir.ui.view", "get_field_translations", [[vista], "arch_db"])[0]
    por_fonte = {}
    for r in traducoes:
        por_fonte.setdefault(r["source"], {})[r["lang"]] = r["value"]

    sem_espanhol = [f for f, langs in por_fonte.items()
                    if langs.get(LINGUA) in (None, "", f)]

    mapa, nao_encontrados = {}, []
    for pt, es in textos.items():
        alvos = [f for f in sem_espanhol if pt in f]
        if not alvos:
            ja = [f for f in por_fonte if pt in f]
            nao_encontrados.append((pt, "já traduzida" if ja else "não existe na página"))
            continue
        for fonte in alvos:
            mapa[fonte] = mapa.get(fonte, fonte).replace(pt, es)
    return mapa, nao_encontrados


def vista_da_pagina(odoo, url):
    p = odoo.search_read("website.page", [["url", "=", url]], ["id", "view_id"])
    if not p:
        raise SystemExit(f"ABORTADO: não encontrei a página {url}.")
    return p[0]["view_id"][0]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true", help="escreve mesmo")
    ap.add_argument("--creds", default=os.path.expanduser("~/.lusosofa_odoo.json"))
    args = ap.parse_args()

    odoo = Odoo(json.load(open(args.creds, encoding="utf-8")))
    modo = "APLICAR" if args.aplicar else "dry-run (não escreve nada)"
    print(f"\nEspanhol em falta [{modo}]")
    print(f"{odoo.url} · base {odoo.db}\n")

    print("antes — português a passar na versão espanhola")
    antes = varrer(odoo.url)
    for pag, linhas in antes.items():
        for l in linhas:
            print(f"  {pag:16} {l[:64]!r}")
    if not antes:
        print("  nada encontrado")

    # --- plano ---------------------------------------------------------------
    menus = []
    for url, (pt, es) in MENUS.items():
        achado = odoo.search_read("website.menu", [["url", "=", url]], ["id"])
        if not achado:
            raise SystemExit(f"ABORTADO: não encontrei o menu {url}.")
        menus.append((achado[0]["id"], pt, es))

    vistas, mapas, falhas = {}, {}, []
    for url, textos in PAGINAS_TERMOS.items():
        vistas[url] = vista_da_pagina(odoo, url)
        mapas[url], nf = mapa_de_termos(odoo, vistas[url], textos)
        falhas += [(url, pt, porque) for pt, porque in nf]

    produtos = []
    publicados = odoo.search_read("product.template", [["is_published", "=", True]], ["id"])
    for p in publicados:
        t = {r["lang"]: r["value"] for r in
             odoo.kw("product.template", "get_field_translations", [[p["id"]], "name"])[0]}
        pt = t.get("pt_PT")
        if pt in PRODUTOS and t.get("es_ES") != PRODUTOS[pt]:
            produtos.append((p["id"], pt, PRODUTOS[pt]))

    print("\nplano")
    for mid, pt, es in menus:
        print(f"  menu {mid:<4}    {pt!r} -> {es!r}")
    for url, textos in PAGINAS_TERMOS.items():
        for pt, es in textos.items():
            estado = "" if any(pt in f for f in mapas[url]) else "   [sem efeito]"
            print(f"  {url:<12} {pt[:46]!r} -> {es[:46]!r}{estado}")
    for url, pt, porque in falhas:
        print(f"  ~ {url:<12} {pt[:46]!r} sem efeito: {porque}")
    for pid, pt, es in produtos:
        print(f"  produto {pid:<4} {pt!r} -> {es!r}")
    print(f"\n  {len(menus)} menu, "
          f"{sum(len(m) for m in mapas.values())} sequências de página, "
          f"{len(produtos)} nomes de produto")

    if not args.aplicar:
        print("\n  Nada foi escrito. Para aplicar: --aplicar\n")
        return

    carimbo = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    destino = RAIZ / f".backup_lusosofa_es_falta_{carimbo}.json"
    destino.write_text(json.dumps({
        "tirado_em_utc": carimbo, "base": odoo.db, "url": odoo.url,
        "accao": "traduzir para espanhol o que ficou por traduzir na passagem de 2026-09-24",
        "portugues_a_passar_antes": antes,
        "menus": [{"id": m, "pt": pt, "es": es} for m, pt, es in menus],
        "vistas": vistas, "termos": PAGINAS_TERMOS, "mapas_resolvidos": mapas,
        "produtos": [{"id": p, "pt": pt, "es": es} for p, pt, es in produtos],
        "como_reverter": "update_field_translations com o valor antigo em cada termo",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n  resguardo: {destino.name}")

    for mid, pt, es in menus:
        odoo.kw("website.menu", "write", [[mid], {"name": es}], {"context": {"lang": LINGUA}})
        print(f"  menu: {pt} -> {es}")
    for url, mapa in mapas.items():
        if not mapa:
            continue
        odoo.kw("ir.ui.view", "update_field_translations",
                [[vistas[url]], "arch_db", {LINGUA: mapa}])
        print(f"  {url}: {len(mapa)} sequências escritas em {LINGUA}")
    for pid, pt, es in produtos:
        odoo.kw("product.template", "update_field_translations", [[pid], "name", {LINGUA: es}])
        print(f"  produto {pid}: {pt} -> {es}")

    # --- verificação ---------------------------------------------------------
    print("\nverificação — contra o que o servidor entrega")
    ok = True

    for mid, pt, es in menus:
        lido = odoo.kw("website.menu", "read", [[mid], ["name"]],
                       {"context": {"lang": LINGUA}})[0]["name"]
        if lido != es:
            print(f"  ! menu {pt}: ficou {lido!r}")
            ok = False

    for url, mapa in mapas.items():
        posto = {t["source"]: t["value"] for t in
                 odoo.kw("ir.ui.view", "get_field_translations", [[vistas[url]], "arch_db"])[0]
                 if t["lang"] == LINGUA}
        for fonte, valor in mapa.items():
            if posto.get(fonte) != valor:
                print(f"  ! {url} {fonte[:50]!r}: ficou {str(posto.get(fonte))[:50]!r}")
                ok = False

    # Nome a nome, sem procurar sinais: é esta a parte que a varredura não faz.
    print("\n  nomes de produto, um a um")
    for p in publicados:
        t = {r["lang"]: r["value"] for r in
             odoo.kw("product.template", "get_field_translations", [[p["id"]], "name"])[0]}
        pt, es = t.get("pt_PT"), t.get("es_ES")
        if es != pt:
            continue
        if pt in IGUAIS_DE_PROPOSITO:
            print(f"    {pt!r} igual de propósito — {IGUAIS_DE_PROPOSITO[pt]}")
        else:
            print(f"  ! {pt!r} continua em português e não está na lista dos iguais")
            ok = False

    depois = varrer(odoo.url)
    for pag, linhas in depois.items():
        for l in linhas:
            print(f"  ! ainda em português: {pag} {l[:64]!r}")
            ok = False
    print(f"\n  as {len(PAGINAS_ES)} páginas espanholas sem português a passar: "
          f"{'sim' if not depois else 'NÃO'}")

    print("\n" + ("Espanhol fechado." if ok else
                  "ATENÇÃO: algo não confere. Vê o resguardo."))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
