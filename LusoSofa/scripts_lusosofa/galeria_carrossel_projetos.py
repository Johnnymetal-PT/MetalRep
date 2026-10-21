#!/usr/bin/env python3
"""Troca a grelha de imagens de /projetos por um carrossel.

Por defeito faz **dry-run**. Para escrever mesmo:

    python3 scripts_lusosofa/galeria_carrossel_projetos.py --aplicar

## O que estava mal, medido

`FACTO OBSERVADO` (2026-09-29): a secção «Algumas peças que fizemos» tinha sete
imagens numa grelha de três colunas, dentro de `pg-frame`, que **não impõe
proporção**. Das sete, cinco são 3:2 deitadas e duas 2:3 ao alto. Cada cartão
ficava com a altura da sua imagem, as filas não fechavam em baixo, e a última
fila ficava com um lugar vazio.

Quem olhou disse que as imagens pareciam «perdidas». Estavam.

## Porquê um carrossel, e o que ele resolve mesmo

Convém separar as duas coisas, porque é fácil dar crédito ao componente errado:

* o desalinhamento resolve-se com **altura uniforme**, e isso resolvia-se na
  grelha na mesma;
* o carrossel resolve outra coisa: sete peças em grelha obrigam a rolar a página
  para as ver todas, e em três colunas sobra sempre um buraco.

A altura é fixa e a largura segue a proporção de cada imagem, **não o
contrário**. A primeira tentativa impôs 3:2 a todos os painéis com recorte ao
centro: alinhava as alturas e cortava as peças — o cadeirão de bouclé ficava sem
as pernas, que numa oficina de estofos são desenho e não margem. Foi vista
renderizada e descartada.

A faixa é **rolável sem JavaScript** — é uma caixa com `overflow-x: auto` e
pontos de encaixe, que já responde ao dedo, ao trackpad e às teclas. As setas
são acrescentadas pelo `pg_movimento.js` e são conforto, não o mecanismo. A
largura dos painéis deixa o seguinte espreitar na margem, que diz que há mais
para ver melhor do que bolinhas por baixo.

## O que este script não resolve

`FACTO OBSERVADO`: duas das sete imagens (2216 e 2218) são **recortes sobre
fundo branco** — detectado pelos quatro cantos —; as outras cinco são
fotografias de ambiente. Numa página preta, os recortes leem-se como buracos,
e isso não é um problema de disposição: é de conteúdo.

Ficam as sete, porque tirar imagens de uma secção do cliente é decisão dele e
não minha. Fica registado aqui para a conversa ser tida com factos.
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

URL = "/projetos"
MARCA = "Algumas peças que fizemos"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true", help="escreve mesmo")
    ap.add_argument("--creds", default=os.path.expanduser("~/.lusosofa_odoo.json"))
    args = ap.parse_args()

    odoo = Odoo(json.load(open(args.creds, encoding="utf-8")))
    modo = "APLICAR" if args.aplicar else "dry-run (não escreve nada)"
    print(f"\nGaleria de {URL} [{modo}]")
    print(f"{odoo.url} · base {odoo.db}\n")

    pagina = odoo.search_read("website.page", [["url", "=", URL]], ["id", "view_id"])
    if not pagina:
        raise SystemExit(f"ABORTADO: não encontrei a página {URL}.")
    vista = pagina[0]["view_id"][0]

    arch = odoo.kw("ir.ui.view", "read", [[vista], ["arch_db"]],
                   {"context": {"lang": "en_US"}})[0]["arch_db"]

    # A secção que contém o título da galeria, e só essa.
    seccao = None
    for m in re.finditer(r"(?s)<section\b.*?</section>", arch):
        if MARCA in m.group(0):
            seccao = m.group(0)
            break
    if seccao is None:
        raise SystemExit(f"ABORTADO: não encontrei a secção de {MARCA!r}.")

    if "pg-carrossel" in seccao:
        print("  a secção já é um carrossel — nada a fazer")
        return

    grelha = re.search(r'(?s)<div class="row">.*?</div>\s*</div>\s*</section>', seccao)
    if not grelha:
        raise SystemExit("ABORTADO: não reconheci a grelha dentro da secção.")

    imagens = re.findall(r'<img\s+src="([^"]+)"\s+alt="([^"]*)"', grelha.group(0))
    if not imagens:
        raise SystemExit("ABORTADO: não encontrei imagens na grelha.")

    paineis = "".join(
        f'<figure class="pg-carrossel-painel">'
        f'<img src="{src}" alt="{alt}" loading="lazy"/></figure>'
        for src, alt in imagens
    )
    novo_bloco = (f'<div class="pg-carrossel"><div class="pg-carrossel-faixa">'
                  f'{paineis}</div></div></div></section>')
    seccao_nova = seccao.replace(grelha.group(0), novo_bloco)

    print(f"  vista {vista}, secção {MARCA!r}")
    print(f"  {len(imagens)} imagens passam de grelha de 3 colunas a painéis do carrossel:")
    for src, alt in imagens:
        print(f"    {src:22} {alt[:58]}")
    print("\n  altura fixa e largura natural — nenhuma imagem é recortada")

    if not args.aplicar:
        print("\n  Nada foi escrito. Para aplicar: --aplicar\n")
        return

    carimbo = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    destino = RAIZ / f".backup_lusosofa_carrossel_{carimbo}.json"
    destino.write_text(json.dumps({
        "tirado_em_utc": carimbo, "base": odoo.db, "url": odoo.url,
        "accao": "trocar a grelha da galeria de /projetos por um carrossel",
        "vista": vista, "arch_db_antes": arch,
        "imagens": [{"src": s, "alt": a} for s, a in imagens],
        "como_reverter": "escrever de volta arch_db_antes em contexto en_US",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n  resguardo: {destino.name}")

    odoo.kw("ir.ui.view", "write", [[vista], {"arch_db": arch.replace(seccao, seccao_nova)}],
            {"context": {"lang": "en_US"}})
    print(f"  secção reescrita na vista {vista}")

    print("\nverificação — contra as páginas servidas")
    ok = True
    for u in [URL, "/es" + URL]:
        r = urllib.request.urlopen(odoo.url + u, timeout=90)
        h = r.read().decode("utf-8", "replace")
        n = h.count("pg-carrossel-painel")
        faltam = [a for _, a in imagens if a and a not in h and "/es" not in u]
        print(f"  {u:14} HTTP {r.status} · {n} painéis")
        if n != len(imagens):
            print(f"    ! esperava {len(imagens)} painéis")
            ok = False
        if faltam:
            print(f"    ! textos alternativos em falta: {len(faltam)}")
            ok = False
        if "pg-frame" in h and MARCA in h[:h.find("pg-frame")]:
            pass  # outras secções podem continuar a usar molduras

    print("\n" + ("Carrossel montado." if ok else
                  "ATENÇÃO: algo não confere. Vê o resguardo."))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
