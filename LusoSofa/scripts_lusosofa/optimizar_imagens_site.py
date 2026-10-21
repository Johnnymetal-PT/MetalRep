#!/usr/bin/env python3
"""Converte as imagens do site para WebP e define a pré-visualização social.

Por defeito faz **dry-run**. Para escrever mesmo:

    python3 scripts_lusosofa/optimizar_imagens_site.py --aplicar

## Porquê

Medido a 2026-09-28: a página inicial pesava 1452 KB, dos quais 950 KB em
imagens — todas em JPEG e nenhuma com `srcset`. Quem abre no telemóvel
descarrega ficheiros de 1536 px para os mostrar a 390.

Duas coisas se corrigem aqui:

* **WebP**, que ao mesmo nível de qualidade pesa tipicamente menos um terço;
* **a largura de cada imagem ajustada ao maior sítio onde aparece** — não
  serve de nada guardar 1536 px numa fotografia que nunca é mostrada acima
  de 480.

O que isto **não** faz é `srcset` verdadeiro, que serviria tamanhos diferentes
conforme o ecrã. Isso depende de como o Odoo monta cada bloco e não se resolve
carregando ficheiros. O ganho aqui é o grosso; o resto é afinação.

**A conversão é destrutiva no anexo, e de propósito**: reescreve o ficheiro
guardado no Odoo em vez de criar outro, para os endereços `/web/image/<id>`
que as páginas já usam continuarem a funcionar. Os originais estão todos no
repositório — `fotos/`, `imagens/` e `proposta_site/` —, por isso nada se
perde que não se reconstrua.

## A pré-visualização social

Quando alguém partilha o site no WhatsApp ou no Facebook, aparecia **o
logótipo sobre preto**: um rectângulo escuro. Passa a aparecer uma sala.
"""

import argparse
import base64
import datetime
import io
import json
import os
import sys
import urllib.request

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aplicar_identidade import Odoo, RAIZ  # noqa: E402

# nome do anexo -> largura máxima, pelo maior sítio onde a imagem aparece
LARGURAS = {
    "lusosofa_sala_modular.jpg": 1600,        # capa, a toda a largura
    "lusosofa_desenho_alcantara.jpg": 1400,   # destaque em 7 colunas
    "lusosofa_capitone_verde.jpg": 1200,      # faixa em 7 colunas
    "lusosofa_seccional_sala.jpg": 1000,      # cartão de categoria
    "lusosofa_cadeiroes_terracota.jpg": 1000,
    "lusosofa_quarto_capitone.jpg": 1000,
}
LARGURA_GALERIA = 900   # tudo o resto só aparece em galerias de 3 ou 4 colunas
QUALIDADE = 78

# A imagem que aparece ao partilhar uma ligação do site.
IMAGEM_SOCIAL = "lusosofa_sala_modular.jpg"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true", help="escreve mesmo")
    ap.add_argument("--creds", default=os.path.expanduser("~/.lusosofa_odoo.json"))
    args = ap.parse_args()

    odoo = Odoo(json.load(open(args.creds, encoding="utf-8")))
    modo = "APLICAR" if args.aplicar else "dry-run (não escreve nada)"
    print(f"\nImagens do site [{modo}]")
    print(f"{odoo.url} · base {odoo.db}\n")

    anexos = odoo.search_read("ir.attachment",
                              [["name", "like", "lusosofa_"], ["public", "=", True]],
                              ["id", "name", "mimetype", "file_size", "datas"])
    if not anexos:
        raise SystemExit("ABORTADO: não encontrei as imagens do site.")

    plano, poupado = [], 0
    for a in sorted(anexos, key=lambda r: r["name"]):
        if a["mimetype"] == "image/webp":
            print(f"  {a['name'][:34]:36} já em WebP")
            continue
        largura = LARGURAS.get(a["name"], LARGURA_GALERIA)
        im = Image.open(io.BytesIO(base64.b64decode(a["datas"]))).convert("RGB")
        w0, h0, kb0 = im.width, im.height, a["file_size"] // 1024
        if im.width > largura:
            im = im.resize((largura, round(im.height * largura / im.width)), Image.LANCZOS)
        saco = io.BytesIO()
        im.save(saco, "WEBP", quality=QUALIDADE, method=6)
        kb1 = len(saco.getvalue()) // 1024
        poupado += kb0 - kb1
        plano.append((a["id"], a["name"], saco.getvalue(), im.width, im.height))
        print(f"  {a['name'][:34]:36} {w0}x{h0} {kb0:>4}KB -> "
              f"{im.width}x{im.height} {kb1:>4}KB")

    print(f"\n  poupança total: {poupado} KB em {len(plano)} imagens")

    site = odoo.search_read("website", [], ["id", "social_default_image"])[0]
    print(f"\n  imagem de partilha definida: "
          f"{'sim' if site['social_default_image'] else 'não — usa o logótipo'}")

    if not args.aplicar:
        print("\n  Nada foi escrito. Para aplicar: --aplicar\n")
        return

    carimbo = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    destino = RAIZ / f".backup_lusosofa_webp_{carimbo}.json"
    destino.write_text(json.dumps({
        "tirado_em_utc": carimbo, "base": odoo.db, "url": odoo.url,
        "accao": "converter as imagens do site para WebP e definir a partilha social",
        "anexos_antes": [{"id": a["id"], "name": a["name"], "mimetype": a["mimetype"],
                          "file_size": a["file_size"]} for a in anexos],
        "social_default_image_antes": bool(site["social_default_image"]),
        "como_reverter": ("recarregar os originais de fotos/, imagens/ e proposta_site/ "
                          "pelos scripts que os carregaram"),
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n  resguardo: {destino.name}")

    for aid, nome, dados, w, h in plano:
        odoo.kw("ir.attachment", "write", [[aid], {
            "datas": base64.b64encode(dados).decode(),
            "mimetype": "image/webp",
            "name": nome.rsplit(".", 1)[0] + ".webp",
        }])
    print(f"  {len(plano)} imagens convertidas")

    social = [a for a in anexos if a["name"] == IMAGEM_SOCIAL]
    if social:
        novo = next((d for i, n, d, w, h in plano if i == social[0]["id"]), None)
        odoo.kw("website", "write", [[site["id"]], {
            "social_default_image": base64.b64encode(novo or base64.b64decode(
                social[0]["datas"])).decode()}])
        print("  imagem de partilha definida a partir da sala com lustre")

    print("\nverificação — contra o que o servidor entrega")
    ok = True
    for aid, nome, _, _, _ in plano:
        with urllib.request.urlopen(f"{odoo.url}/web/image/{aid}", timeout=60) as r:
            tipo = r.headers.get("content-type", "")
            tamanho = len(r.read())
        bom = "webp" in tipo
        if not bom:
            print(f"  ! /web/image/{aid} devolve {tipo}")
            ok = False
    print(f"  as {len(plano)} imagens são servidas em WebP: {'sim' if ok else 'NÃO'}")

    h = urllib.request.urlopen(odoo.url + "/", timeout=90).read().decode("utf-8", "replace")
    import re
    og = re.search(r'<meta[^>]*og:image[^>]*content="([^"]+)"', h)
    valor = og.group(1) if og else "(nenhum)"
    logo = "logo" in valor
    print(f"  og:image: {valor[:72]}")
    print(f"  deixou de ser o logótipo: {'sim' if not logo else 'NÃO'}")
    ok = ok and not logo

    print("\n" + ("Imagens optimizadas." if ok else
                  "ATENÇÃO: algo não confere. Vê o resguardo."))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
