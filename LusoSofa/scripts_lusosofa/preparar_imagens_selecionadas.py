#!/usr/bin/env python3
"""Prepara as cinco fotografias escolhidas e coloca-as na página «História».

Por defeito faz **dry-run**. Para escrever mesmo:

    python3 scripts_lusosofa/preparar_imagens_selecionadas.py --aplicar

## A escolha

De 35 ficheiros em ``fotos/`` há 27 imagens distintas: oito são duplicados em
pior resolução, e treze só existem a 512 px ou menos — quase todas repetindo
produtos que a loja já mostra melhor. Sobram poucas que valham a pena, e são
estas.

A melhor de todas é o **desenho a lápis assinado «Alcântara»**: é a única
imagem da pasta que não se compra num banco de imagens, e mostra o trabalho de
projecto que a página «História» descreve por palavras.

## Onde ficam, e porquê aí

Na página «História», que hoje é uma parede de texto sem uma única imagem. Não
vão para ``/projetos``, cuja galeria é de **peças feitas por encomenda** — estas
são renders de ambiente e um desenho de estúdio, e misturá-las diluiria o
sentido daquela.

A legenda do desenho diz apenas «Estudo do modelo Alcântara», que é o que está
escrito no próprio desenho. As restantes não levam legenda: não sei que peça é
qual, e uma legenda errada afirma sobre o produto do cliente o que ninguém
confirmou.

## O tratamento

Redimensionar para 1600 px no lado maior — nunca ampliar, que só aumenta o
ficheiro sem acrescentar detalhe —, qualidade 82 e progressivo. Os metadados
saem: fotografias de telemóvel trazem coordenadas de GPS, e o sítio de onde
foram tiradas não tem de ir no ficheiro que se publica.
"""

import argparse
import base64
import datetime
import io
import json
import os
import re
import sys
import urllib.request
import xml.dom.minidom

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aplicar_identidade import Odoo, RAIZ  # noqa: E402

PASTA = RAIZ / "fotos"
LADO_MAXIMO = 1600
QUALIDADE = 82
URL_PAGINA = "/about-us"

# ficheiro -> (nome no Odoo, texto alternativo, legenda ou None)
ESCOLHIDAS = [
    ("677DF460-BAFB-4C05-A170-8758B6B0B1C2.jpeg",
     "lusosofa_desenho_alcantara.jpg",
     "Desenho a lápis de um sofá, assinado Alcântara",
     "Estudo do modelo Alcântara."),
    ("FD83E35C-D1FE-4CD0-A630-9A866FE50B27.jpeg",
     "lusosofa_quarto_capitone.jpg",
     "Quarto com cama de cabeceira alta em capitoné e laterais em aba",
     None),
    ("8E1BB1F3-47BA-45EB-8896-3F87A8413D08_1_105_c.jpeg",
     "lusosofa_sala_lustre.jpg",
     "Sofá modular claro numa sala ampla, com lustre de cristal",
     None),
    ("70B4C865-75DD-4209-B7F6-012ED6D35B8F_1_105_c.jpeg",
     "lusosofa_canto_azul.jpg",
     "Sofá de canto em tecido azul-marinho, com apoios de cabeça e pés metálicos",
     None),
    ("DDF582CD-BEA6-41BD-AB94-2F4D5F85A8CC.jpeg",
     "lusosofa_sofa_verde.jpg",
     "Sofá em veludo verde-esmeralda, com pés em madeira clara",
     None),
]


def optimizar(caminho):
    """Devolve (bytes, largura, altura, tamanho original em KB)."""
    original = caminho.stat().st_size // 1024
    im = Image.open(caminho)
    im = im.convert("RGB")
    if max(im.size) > LADO_MAXIMO:
        escala = LADO_MAXIMO / max(im.size)
        im = im.resize((round(im.width * escala), round(im.height * escala)),
                       Image.LANCZOS)
    saco = io.BytesIO()
    # Sem `exif=`: os metadados não são copiados, e é isso que se quer.
    im.save(saco, "JPEG", quality=QUALIDADE, optimize=True, progressive=True)
    return saco.getvalue(), im.width, im.height, original


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true", help="escreve mesmo")
    ap.add_argument("--creds", default=os.path.expanduser("~/.lusosofa_odoo.json"))
    args = ap.parse_args()

    odoo = Odoo(json.load(open(args.creds, encoding="utf-8")))
    modo = "APLICAR" if args.aplicar else "dry-run (não escreve nada)"
    print(f"\nImagens escolhidas para {URL_PAGINA} [{modo}]")
    print(f"{odoo.url} · base {odoo.db}\n")

    preparadas = []
    for ficheiro, nome, alt, legenda in ESCOLHIDAS:
        caminho = PASTA / ficheiro
        if not caminho.exists():
            raise SystemExit(f"ABORTADO: não encontrei {caminho}")
        dados, w, h, antes = optimizar(caminho)
        depois = len(dados) // 1024
        seta = "=" if w == Image.open(caminho).width else "->"
        print(f"  {nome:34} {Image.open(caminho).width}x{Image.open(caminho).height} "
              f"{seta} {w}x{h}   {antes}KB -> {depois}KB")
        preparadas.append((nome, alt, legenda, dados))

    urls = {}
    for nome, alt, legenda, dados in preparadas:
        ja = odoo.search_read("ir.attachment", [["name", "=", nome], ["public", "=", True]],
                              ["id"])
        if ja:
            urls[nome] = f"/web/image/{ja[0]['id']}"
            print(f"  {nome}: já carregado (id {ja[0]['id']})")
        elif args.aplicar:
            att = odoo.kw("ir.attachment", "create", [{
                "name": nome, "datas": base64.b64encode(dados).decode(),
                "mimetype": "image/jpeg", "public": True,
                "res_model": "ir.ui.view", "res_id": 0,
            }])
            urls[nome] = f"/web/image/{att}"
            print(f"  {nome}: carregado (id {att})")

    pag = [p for p in odoo.search_read("website.page", [["url", "=", URL_PAGINA]],
                                       ["id", "view_id", "is_published"]) if p["is_published"]]
    if len(pag) != 1:
        raise SystemExit(f"ABORTADO: esperava uma página publicada em {URL_PAGINA}.")
    vid = pag[0]["view_id"][0]
    antes_arch = odoo.kw("ir.ui.view", "read", [[vid], ["arch_db"]],
                         {"context": {"lang": "en_US"}})[0]["arch_db"]

    limpo = re.sub(r'\s*<section[^>]*data-name="Galeria"[^>]*>.*?</section>\n?',
                   "", antes_arch, flags=re.S)
    if limpo != antes_arch:
        print("\n  galeria anterior encontrada — vai ser substituída")

    if not args.aplicar:
        print(f"\n  [dry-run] montaria a galeria em {URL_PAGINA}")
        print("\n  Nada foi escrito. Para aplicar: --aplicar\n")
        return

    def moldura(nome, alt, legenda):
        bloco = (f'<div class="pg-frame mb-3"><img src="{urls[nome]}" alt="{alt}" '
                 f'class="img img-fluid" loading="lazy"/></div>')
        if legenda:
            bloco += f'<p class="pg-eyebrow">{legenda}</p>'
        return bloco

    destaque, resto = preparadas[0], preparadas[1:]
    seccao = (
        '                <section class="s_text_block pt16 pb64 o_cc o_cc1" '
        'data-snippet="s_text_block" data-name="Galeria">\n'
        '                    <div class="container">\n'
        '                        <div class="row">\n'
        '                            <div class="col-lg-8 offset-lg-2 mb-5">'
        f'{moldura(destaque[0], destaque[1], destaque[2])}</div>\n'
        '                        </div>\n'
        '                        <div class="row">\n'
        + "".join(f'                            <div class="col-12 col-md-6 col-lg-3">'
                  f'{moldura(n, a, None)}</div>\n' for n, a, _, _ in resto)
        + '                        </div>\n'
        '                    </div>\n'
        '                </section>\n'
    )
    # Ancorar pelo fim do documento, não por uma indentação exacta.
    #
    # A primeira versão procurava a cadeia literal que a página /projetos usa —
    # mas essa página fui eu que a escrevi, e a «História» foi montada no editor
    # do site, com outra indentação. A âncora não bateu e o script parou.
    #
    # O que é estável em qualquer página do Odoo é a forma do fecho: o último
    # </div> (o do wrap) seguido dos dois </t>. Os espaços entre eles variam com
    # quem editou a página pela última vez, e por isso não se contam.
    fecho = re.compile(r"(</div>\s*</t>\s*</t>\s*)$")
    if not fecho.search(limpo):
        raise SystemExit("ABORTADO: não reconheci o fecho da página.")
    novo = fecho.sub(lambda m: seccao + m.group(1), limpo, count=1)

    try:
        xml.dom.minidom.parseString(novo.replace("t-call=", "data-t-call="))
    except Exception as e:
        raise SystemExit(f"ABORTADO: o resultado não é XML válido — {e}")

    carimbo = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    destino = RAIZ / f".backup_lusosofa_galeria_historia_{carimbo}.json"
    destino.write_text(json.dumps({
        "tirado_em_utc": carimbo, "base": odoo.db, "url": odoo.url,
        "accao": f"galeria de imagens escolhidas em {URL_PAGINA}",
        "vista": vid, "arch_db_antes": antes_arch, "urls": urls,
        "como_reverter": f"ir.ui.view write [[{vid}], {{'arch_db': <arch_db_antes>}}] com lang en_US",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n  resguardo: {destino.name}")

    odoo.kw("ir.ui.view", "write", [[vid], {"arch_db": novo}], {"context": {"lang": "en_US"}})
    print(f"  {URL_PAGINA}: galeria de {len(preparadas)} imagens inserida")

    odoo.kw("ir.ui.view", "update_field_translations",
            [[vid], "arch_db", {"es_ES": {"Estudo do modelo Alcântara.":
                                          "Estudio del modelo Alcântara."}}])
    print("  legenda traduzida para espanhol")

    print("\nverificação — contra as páginas servidas")
    ok = True
    for caminho in [URL_PAGINA, "/es" + URL_PAGINA]:
        h = urllib.request.urlopen(odoo.url + caminho, timeout=90).read().decode("utf-8", "replace")
        n = len([u for u in urls.values() if u in h])
        print(f"  {caminho:16} imagens presentes: {n}/{len(urls)}")
        ok = ok and n == len(urls)
    for nome, url in urls.items():
        cod = urllib.request.urlopen(odoo.url + url, timeout=60).status
        if cod != 200:
            print(f"  ! {nome}: HTTP {cod}")
            ok = False
    print(f"  as {len(urls)} imagens respondem 200: {'sim' if ok else 'NÃO'}")

    pt = urllib.request.urlopen(odoo.url + URL_PAGINA, timeout=90).read().decode("utf-8", "replace")
    es = urllib.request.urlopen(odoo.url + "/es" + URL_PAGINA, timeout=90).read().decode("utf-8", "replace")
    for pagina, texto, lingua in [(pt, "Estudo do modelo Alcântara", "pt"),
                                  (es, "Estudio del modelo Alcântara", "es")]:
        print(f"  legenda em {lingua}: {'sim' if texto in pagina else 'NÃO'}")
        ok = ok and texto in pagina

    print("\n" + ("Imagens no ar." if ok else "ATENÇÃO: algo não confere. Vê o resguardo."))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
