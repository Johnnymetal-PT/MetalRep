#!/usr/bin/env python3
"""Carrega fotografias para o Odoo e coloca-as na página ``/projetos``.

Por defeito faz **dry-run**. Para escrever mesmo:

    python3 scripts_lusosofa/carregar_imagens.py --aplicar

## O que ficou de fora, e porquê

Das dez imagens em ``imagens/``, três não entram — e a razão não é qualidade:

* ``EBE9B139`` é uma **captura de ecrã do Pinterest**, com a barra do site e o
  título da publicação à vista;
* ``2EE35B37`` é uma **captura de ecrã de uma story de Instagram**, com a
  interface da aplicação visível;
* ``FD07A8C4`` é uma **folha de mockup** comercial, com o título «MODERN SOFA»
  e texto *lorem ipsum*.

As duas primeiras são de terceiros. Publicá-las no site de um cliente é usar
trabalho de outra pessoa sem licença, e o facto de estarem na pasta do projeto
não muda isso — provavelmente foram guardadas como referência visual, que é uso
legítimo e diferente. A terceira é um ficheiro de demonstração de um banco de
imagens; sairia no site com «lorem ipsum» impresso.

## O que este script não faz

Não atribui fotografias aos modelos da Coleção Traços. Ninguém me disse qual
das peças é a Noa, a Porto, a Estoril ou a Alcântara, e pôr uma legenda errada
debaixo de uma fotografia é afirmar sobre o produto do cliente uma coisa que
não sei. Essas ficam à espera de quem saiba.

As imagens colocadas aqui vão para a página de trabalho por encomenda, onde
ilustram sem nomear — que é o uso que não exige esse conhecimento.
"""

import argparse
import base64
import datetime
import json
import os
import pathlib
import re
import sys
import urllib.request
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aplicar_identidade import Odoo, RAIZ  # noqa: E402

PASTA = RAIZ / "imagens"

# Ficheiro -> (nome no Odoo, texto alternativo).
#
# O que estas fotografias são, confirmado a 2026-09-26: peças feitas por
# encomenda, guardadas por serem bonitas. **Não são artigos à venda** nem os
# modelos da Coleção Traços que a página inicial nomeia. Daí viverem na página
# de trabalho por encomenda e não na loja, e daí nenhuma legenda nomear nada:
# descrevem o que se vê, que é tudo o que se pode afirmar.
IMAGENS = {
    "55F70B81-2882-4A23-A015-89E421E3CECB.jpeg": (
        "lusosofa_sofa_canelado.jpg",
        "Sofá de encosto canelado em tecido claro, com pés metálicos dourados",
    ),
    "8CCA9591-8B2B-4988-9DEB-401DE9E8E22F.jpeg": (
        "lusosofa_sala_modular.jpg",
        "Sofá modular de linhas curvas numa sala ampla com luz natural",
    ),
    "D05BFE40-6D66-4931-ABFE-C50275CF114D.jpeg": (
        "lusosofa_cadeirao_boucle.jpg",
        "Cadeirão em tecido bouclé claro com estrutura em madeira maciça",
    ),
    "5B2A4695-1B06-42EC-93CA-97336194EF44.jpeg": (
        "lusosofa_cadeiroes_terracota.jpg",
        "Par de cadeirões de braços arredondados em tecido terracota",
    ),
    "AEE40AE1-A867-4CA9-9E4A-2173BCE7EEE9.jpeg": (
        "lusosofa_seccional_sala.jpg",
        "Sofá seccional com chaise longue em tecido cinzento texturado",
    ),
    "C19AF2BE-8C50-4C01-AC46-7A95BBD651D2.jpeg": (
        "lusosofa_cadeirao_showroom.jpg",
        "Cadeirão em bouclé com estrutura em madeira, fotografado no showroom",
    ),
    "928ACB18-FD32-4720-B73F-986CC2365CD4.jpeg": (
        "lusosofa_quarto_cadeirao.jpg",
        "Quarto com cabeceira estofada e cadeirão de braços arredondados",
    ),
}

NAO_USAR = {
    "EBE9B139-EE9F-42E7-A75B-1B9B77696773.jpeg": "captura de ecrã do Pinterest",
    "2EE35B37-DD96-4D37-9761-73DDADAE3618.jpeg": "captura de ecrã de story de Instagram",
    "FD07A8C4-BD22-4E06-A829-EF252D2C0EC8.jpeg": "folha de mockup com lorem ipsum",
}

URL_PAGINA = "/projetos"


def carregar(odoo, ficheiro, nome, escrever):
    """Cria (ou reutiliza) o anexo público e devolve o caminho /web/image/<id>."""
    ja = odoo.search_read("ir.attachment", [["name", "=", nome], ["public", "=", True]],
                          ["id", "name"])
    if ja:
        print(f"   {nome}: já existe (id {ja[0]['id']})")
        return f"/web/image/{ja[0]['id']}"
    if not escrever:
        print(f"   [dry-run] carregaria {nome} ({ficheiro.stat().st_size // 1024} KB)")
        return None
    att = odoo.kw("ir.attachment", "create", [{
        "name": nome,
        "datas": base64.b64encode(ficheiro.read_bytes()).decode(),
        "mimetype": "image/jpeg",
        "public": True,
        "res_model": "ir.ui.view",
        "res_id": 0,
    }])
    print(f"   {nome}: carregado (id {att})")
    return f"/web/image/{att}"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true", help="escreve mesmo")
    ap.add_argument("--creds", default=os.path.expanduser("~/.lusosofa_odoo.json"))
    args = ap.parse_args()

    odoo = Odoo(json.load(open(args.creds, encoding="utf-8")))
    modo = "APLICAR" if args.aplicar else "dry-run (não escreve nada)"
    print(f"\nImagens para {URL_PAGINA} [{modo}]")
    print(f"{odoo.url} · base {odoo.db}\n")

    print("deixadas de fora, por não serem da LusoSofá:")
    for f, porque in NAO_USAR.items():
        existe = (PASTA / f).exists()
        print(f"   {'·' if existe else '?'} {f[:12]}…  {porque}")

    print("\na carregar:")
    urls = {}
    for f, (nome, alt) in IMAGENS.items():
        caminho = PASTA / f
        if not caminho.exists():
            raise SystemExit(f"ABORTADO: não encontrei {caminho}")
        urls[f] = (carregar(odoo, caminho, nome, args.aplicar), alt)

    pag = [p for p in odoo.search_read("website.page", [["url", "=", URL_PAGINA]],
                                       ["id", "view_id", "is_published"]) if p["is_published"]]
    if len(pag) != 1:
        raise SystemExit(f"ABORTADO: esperava uma página publicada em {URL_PAGINA}.")
    vid = pag[0]["view_id"][0]
    antes = odoo.kw("ir.ui.view", "read", [[vid], ["arch_db"]],
                    {"context": {"lang": "en_US"}})[0]["arch_db"]

    # Idempotente: uma galeria anterior é substituída, não duplicada.
    limpo = re.sub(
        r'\s*<section[^>]*data-name="Imagens"[^>]*>.*?</section>\n?', "", antes, flags=re.S)
    if limpo != antes:
        print("\n  galeria anterior encontrada — vai ser substituída")

    if not args.aplicar:
        print(f"\n  [dry-run] montaria uma galeria de {len(IMAGENS)} imagens em {URL_PAGINA}")
        print("\n  Nada foi escrito. Para aplicar: --aplicar\n")
        return
    antes_original, antes = antes, limpo

    # A moldura é a mesma das fichas de produto: passe-partout de linho com
    # filete dourado. As fotografias têm fundo claro e o site é preto — sem
    # moldura ficariam a flutuar como recortes mal feitos.
    def bloco(chave):
        url, alt = urls[chave]
        return (f'<div class="pg-frame mb-4">'
                f'<img src="{url}" alt="{alt}" class="img img-fluid" loading="lazy"/></div>')

    # Uma secção nova antes do fecho do wrap, e só isso.
    #
    # A primeira versão disto tentava enfiar as imagens no meio de uma secção
    # existente, encaixando à letra nas etiquetas de fecho que julgava estarem
    # lá. Acertou em parte e deixou a marcação desequilibrada — a validação
    # apanhou-o, mas o modo de falha merece ficar escrito: contar `</div>` de
    # cabeça num documento que outra pessoa pode ter editado no editor do site
    # é frágil por construção. O fecho do `wrap` é estrutura do Odoo e está
    # sempre lá.
    alvo = '            </div>\n        </div>\n    </t>\n</t>'
    if antes.count(alvo) != 1:
        raise SystemExit(
            f"ABORTADO: esperava um fecho de wrap, encontrei {antes.count(alvo)}."
        )
    # Três colunas em ecrã largo, duas em tablet, uma no telemóvel. As
    # fotografias têm proporções diferentes — umas ao alto, outras ao baixo —
    # e por isso não se força altura igual: recortá-las para alinhar uma grelha
    # é perder justamente o enquadramento que quem as tirou escolheu.
    chaves = list(IMAGENS)
    colunas = "".join(
        f'                            <div class="col-12 col-md-6 col-lg-4">{bloco(k)}</div>\n'
        for k in chaves
    )
    seccao = (
        '                <section class="s_text_block pt16 pb64 o_cc o_cc1" '
        'data-snippet="s_text_block" data-name="Imagens">\n'
        '                    <div class="container">\n'
        '                        <h2>Algumas peças que fizemos</h2>\n'
        '                        <hr class="pg-rule"/>\n'
        '                        <p class="mb-5">Trabalhos por encomenda, cada um '
        'pensado para o espaço a que se destinava.</p>\n'
        '                        <div class="row">\n'
        f'{colunas}'
        '                        </div>\n'
        '                    </div>\n'
        '                </section>\n'
    )
    novo = antes.replace(alvo, seccao + alvo, 1)

    try:
        xml.dom.minidom.parseString(novo.replace("t-call=", "data-t-call="))
    except Exception as e:
        raise SystemExit(f"ABORTADO: o resultado não é XML válido — {e}")

    carimbo = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    destino = RAIZ / f".backup_lusosofa_imagens_{carimbo}.json"
    destino.write_text(json.dumps({
        "tirado_em_utc": carimbo, "base": odoo.db, "url": odoo.url,
        "accao": f"carregar imagens e inseri-las em {URL_PAGINA}",
        # O original, não a versão já sem a galeria anterior: um resguardo que
        # guarda um estado intermédio não repõe nada.
        "vista": vid, "arch_db_antes": antes_original,
        "urls": {k: v[0] for k, v in urls.items()},
        "como_reverter": f"ir.ui.view write [[{vid}], {{'arch_db': <arch_db_antes>}}] com lang en_US",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n  resguardo: {destino.name}")

    odoo.kw("ir.ui.view", "write", [[vid], {"arch_db": novo}], {"context": {"lang": "en_US"}})
    print(f"  {URL_PAGINA}: galeria de {len(IMAGENS)} imagens inserida")

    # O site é bilingue: texto novo sem tradução sai em português no /es, e
    # ninguém dá por isso a não ser que vá lá ver.
    espanhol = {
        "Algumas peças que fizemos": "Algunas piezas que hemos hecho",
        "Trabalhos por encomenda, cada um pensado para o espaço a que se destinava.":
            "Trabajos por encargo, cada uno pensado para el espacio al que se destinaba.",
    }
    odoo.kw("ir.ui.view", "update_field_translations",
            [[vid], "arch_db", {"es_ES": espanhol}])
    print(f"  traduzidos {len(espanhol)} termos para espanhol")

    print("\nverificação — contra as páginas servidas")
    ok = True
    for caminho, titulo in [(URL_PAGINA, "Algumas peças que fizemos"),
                            ("/es" + URL_PAGINA, "Algunas piezas que hemos hecho")]:
        h = urllib.request.urlopen(odoo.url + caminho, timeout=90).read().decode("utf-8", "replace")
        n = len(re.findall(r'<img[^>]+/web/image/\d+', h))
        tem = titulo in h
        marca = "  " if n == len(IMAGENS) and tem else "! "
        print(f"{marca}{caminho:16} imagens: {n}/{len(IMAGENS)}   título traduzido: "
              f"{'sim' if tem else 'NÃO'}")
        ok = ok and n == len(IMAGENS) and tem
    for url, alt in urls.values():
        cod = urllib.request.urlopen(odoo.url + url, timeout=60).status
        print(f"  {url}: HTTP {cod}")
        ok = ok and cod == 200

    print("\n" + ("Imagens no ar." if ok else "ATENÇÃO: algo não confere. Vê o resguardo."))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
