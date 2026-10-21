#!/usr/bin/env python3
"""Escreve as descrições dos 12 artigos publicados, em português e espanhol.

Por defeito faz **dry-run**. Para escrever mesmo:

    python3 scripts_lusosofa/descricoes_produtos.py --aplicar

## O que estas descrições podem e não podem dizer

Foram escritas a olhar para a fotografia de cada peça, e dizem apenas o que aí
se vê: a forma, o acabamento, o desenho do estofo, o tipo de pé. Decisão de
2026-09-25, depois de a alternativa — esperar pelas fichas técnicas do cliente
— ficar sem prazo à vista.

**Não há aqui uma única medida, composição de tecido, opção de configuração ou
prazo de entrega.** Não é omissão: é o limite do que se pode afirmar sobre o
produto de outra pessoa a partir de uma fotografia. Uma descrição que invente
«150 cm de largura» ou «espuma de alta densidade» é pior do que descrição
nenhuma, porque ninguém a consegue desmentir antes de o cliente a ler.

Quando as fichas técnicas chegarem, estas descrições ganham um segundo
parágrafo com os factos. Até lá, dizem a verdade e param aí.

## Onde ficam

No ``description_sale``, que é o que a loja mostra na página do artigo. O texto
português vai para a origem — como em todo o resto deste site — e o espanhol
para a tradução, para as duas versões da loja dizerem o mesmo.
"""

import argparse
import datetime
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aplicar_identidade import Odoo, RAIZ  # noqa: E402

# nome do artigo -> (português, espanhol)
DESCRICOES = {
    "BALI MODULAR": (
        "Sofá modular de linhas rectas, com assentos amplos e braços baixos. "
        "Compõe-se por módulos, incluindo um de chaise longue, o que permite "
        "ajustá-lo à planta da sala. Estofo em tecido cor de areia.",
        "Sofá modular de líneas rectas, con asientos amplios y brazos bajos. "
        "Se compone por módulos, incluido uno de chaise longue, lo que permite "
        "ajustarlo a la planta del salón. Tapizado en tejido color arena.",
    ),
    "SOFÁ SWEET": (
        "Sofá de três lugares com assento e costas em canelado vertical, braços "
        "curvos e pés metálicos dourados. O desenho arredondado e o aspecto "
        "aveludado do tecido dão-lhe presença de sala formal.",
        "Sofá de tres plazas con asiento y respaldo en acanalado vertical, "
        "brazos curvos y patas metálicas doradas. El diseño redondeado y el "
        "aspecto aterciopelado del tejido le dan presencia de salón formal.",
    ),
    "CHAISELONG KENEDY": (
        "Sofá de canto com chaise longue, assentos profundos e apoios de cabeça "
        "independentes. Os braços largos levam canelado na face exterior, e o "
        "conjunto assenta direito ao chão.",
        "Sofá rinconera con chaise longue, asientos profundos y cabezales "
        "independientes. Los brazos anchos llevan acanalado en la cara exterior, "
        "y el conjunto se apoya directamente en el suelo.",
    ),
    "CHAISELONG SINGAPURA": (
        "Sofá de canto com chaise longue, em tecido texturado claro. Os apoios de "
        "cabeça e o encosto levam pesponto canelado, e o conjunto assenta em pés "
        "cónicos escuros que o levantam do chão.",
        "Sofá rinconera con chaise longue, en tejido texturado claro. Los "
        "cabezales y el respaldo llevan pespunte acanalado, y el conjunto se "
        "apoya en patas cónicas oscuras que lo elevan del suelo.",
    ),
    "CADEIRÃO EMILY GIRATÓRIO": (
        "Cadeirão giratório de forma envolvente, com costas e braços em tecido de "
        "xadrez miúdo e assento liso a contrastar. Assenta num aro metálico dourado.",
        "Sillón giratorio de forma envolvente, con respaldo y brazos en tejido de "
        "cuadros menudos y asiento liso que contrasta. Se apoya en un aro "
        "metálico dorado.",
    ),
    "CADEIRÃO SOFY GIRATÓRIO": (
        "Cadeirão giratório inteiramente estofado, de costas curvas e braços "
        "envolventes. O tecido bouclé claro e a ausência de arestas dão-lhe um "
        "volume macio, sem base à vista.",
        "Sillón giratorio totalmente tapizado, de respaldo curvo y brazos "
        "envolventes. El tejido bouclé claro y la ausencia de aristas le dan un "
        "volumen suave, sin base a la vista.",
    ),
    "CADEIRÃO OSLO": (
        "Cadeirão de estrutura em madeira maciça à vista, com assento estofado e "
        "encosto em rolo. O contraste entre a madeira escura e o bouclé claro "
        "deixa a construção da peça à mostra.",
        "Sillón de estructura en madera maciza a la vista, con asiento tapizado y "
        "respaldo en rollo. El contraste entre la madera oscura y el bouclé claro "
        "deja la construcción de la pieza a la vista.",
    ),
    "CAMA SALLY": (
        "Cama estofada com cabeceira alta em canelado vertical, prolongada por "
        "painéis laterais que alargam o conjunto à largura da parede. Os painéis "
        "integram tomadas eléctricas.",
        "Cama tapizada con cabecero alto en acanalado vertical, prolongado por "
        "paneles laterales que amplían el conjunto al ancho de la pared. Los "
        "paneles integran tomas de corriente.",
    ),
    "CABECEIRA CAPITONÉ": (
        "Cabeceira em capitoné, com o botão puxado a formar losangos regulares em "
        "toda a superfície. O veludo verde-petróleo dá-lhe presença num quarto de "
        "tons neutros.",
        "Cabecero en capitoné, con el botón tirado formando rombos regulares en "
        "toda la superficie. El terciopelo verde petróleo le da presencia en un "
        "dormitorio de tonos neutros.",
    ),
    "CABECEIRA MOLY": (
        "Cabeceira de faixas horizontais almofadadas, cortadas ao centro por um "
        "motivo em X num tecido de textura diferente. O jogo entre os dois "
        "acabamentos faz o desenho, sem recorrer a botões.",
        "Cabecero de franjas horizontales acolchadas, cortadas en el centro por un "
        "motivo en X en un tejido de textura distinta. El juego entre los dos "
        "acabados construye el dibujo, sin recurrir a botones.",
    ),
    "CABECEIRA OUROS": (
        "Cabeceira com painéis almofadados dispostos em ouros, o desenho que dá "
        "nome à peça. O relevo faz-se pelo corte e pelo enchimento, e não por "
        "botão, o que lhe dá uma leitura mais limpa.",
        "Cabecero con paneles acolchados dispuestos en rombos, el dibujo que da "
        "nombre a la pieza. El relieve se consigue por el corte y el relleno, y no "
        "por botón, lo que le da una lectura más limpia.",
    ),
    "CABECEIRA QUADRADOS PUXADOS": (
        "Cabeceira de quadrícula puxada, com o ponto a marcar uma malha regular de "
        "quadrados. Em tom cru, é a mais discreta das cabeceiras — o desenho lê-se "
        "pela sombra e não pela cor.",
        "Cabecero de cuadrícula tirada, con el punto marcando una malla regular de "
        "cuadrados. En tono crudo, es el más discreto de los cabeceros: el dibujo "
        "se lee por la sombra y no por el color.",
    ),
}

# Nunca, sem ficha técnica do cliente. A lista existe para quem vier a seguir
# não achar que foram esquecidos.
PROIBIDO = ["cm", "mm", "kg", "densidade", "espuma", "poliéster", "algodão",
            "prazo de entrega", "garantia", "lugares e meio"]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true", help="escreve mesmo")
    ap.add_argument("--creds", default=os.path.expanduser("~/.lusosofa_odoo.json"))
    args = ap.parse_args()

    odoo = Odoo(json.load(open(args.creds, encoding="utf-8")))
    modo = "APLICAR" if args.aplicar else "dry-run (não escreve nada)"
    print(f"\nDescrições dos artigos [{modo}]")
    print(f"{odoo.url} · base {odoo.db}\n")

    # Uma descrição que prometa o que não se sabe é pior do que nenhuma.
    for nome, (pt, es) in DESCRICOES.items():
        for termo in PROIBIDO:
            if termo in pt.lower() or termo in es.lower():
                raise SystemExit(
                    f"ABORTADO: a descrição de {nome} contém {termo!r}, que é um "
                    f"facto técnico que ninguém confirmou."
                )

    produtos = odoo.search_read("product.template", [["is_published", "=", True]],
                                ["id", "name", "description_sale"])
    porNome = {p["name"]: p for p in produtos}

    faltam = [n for n in DESCRICOES if n not in porNome]
    sobram = [p["name"] for p in produtos if p["name"] not in DESCRICOES]
    if faltam:
        raise SystemExit(f"ABORTADO: não encontrei estes artigos no catálogo: {faltam}")
    if sobram:
        print(f"  ! artigos publicados sem descrição escrita: {sobram}\n")

    print(f"  {len(produtos)} artigos publicados, {len(DESCRICOES)} descrições preparadas\n")
    for nome in sorted(DESCRICOES):
        ja = (porNome[nome]["description_sale"] or "").strip()
        estado = "já tem (vai ser substituída)" if ja else "vazia"
        print(f"  {nome:30} {estado}")
        print(f"     {DESCRICOES[nome][0][:96]}…")

    if not args.aplicar:
        print("\n  Nada foi escrito. Para aplicar: --aplicar\n")
        return

    carimbo = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    destino = RAIZ / f".backup_lusosofa_descricoes_{carimbo}.json"
    destino.write_text(json.dumps({
        "tirado_em_utc": carimbo, "base": odoo.db, "url": odoo.url,
        "accao": "escrever description_sale dos 12 artigos, em pt e es",
        "antes": [{"id": p["id"], "name": p["name"],
                   "description_sale": p["description_sale"]} for p in produtos],
        "como_reverter": "repor description_sale de cada artigo com os valores acima",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n  resguardo: {destino.name}")

    # `FACTO OBSERVADO` (2026-09-28): escrever a tradução com `lang` no contexto
    # **substitui a origem**. Fez-se assim à primeira e as três línguas ficaram
    # com o texto espanhol — incluindo a portuguesa, que passou a mostrar
    # «Sillón de estructura…» na loja.
    #
    # O `write` com contexto de língua serve para campos traduzidos por termo
    # já povoados; num campo traduzido por registo ainda vazio, o valor propaga
    # para todas as línguas. A via correcta é a mesma das vistas:
    # `update_field_translations`, que aqui recebe {lingua: valor} directamente,
    # por o campo não ser traduzido termo a termo.
    for nome, (pt, es) in DESCRICOES.items():
        pid = porNome[nome]["id"]
        odoo.kw("product.template", "write", [[pid], {"description_sale": pt}],
                {"context": {"lang": "en_US"}})
        odoo.kw("product.template", "update_field_translations",
                [[pid], "description_sale", {"es_ES": es}])
        print(f"  {nome}")

    print("\nverificação — contra o servidor e contra a loja")
    ok = True
    for lang, esperado in [("pt_PT", 0), ("es_ES", 1)]:
        lidos = odoo.kw("product.template", "read",
                        [[porNome[n]["id"] for n in DESCRICOES], ["name", "description_sale"]],
                        {"context": {"lang": lang}})
        maus = [r["name"] for r in lidos
                if (r["description_sale"] or "").strip() != DESCRICOES[r["name"]][esperado]]
        print(f"  {lang}: {len(lidos) - len(maus)}/{len(lidos)} conferem")
        ok = ok and not maus

    # O que conta é a página que o visitante recebe.
    for caminho, nome, idx in [("/shop/caderiao-oslo-20", "CADEIRÃO OSLO", 0),
                               ("/es/shop/caderiao-oslo-20", "CADEIRÃO OSLO", 1)]:
        try:
            h = urllib.request.urlopen(odoo.url + caminho, timeout=90).read().decode("utf-8", "replace")
            trecho = DESCRICOES[nome][idx][:40]
            print(f"  {caminho}: {'mostra a descrição' if trecho in h else 'NÃO mostra'}")
            ok = ok and trecho in h
        except Exception as e:
            print(f"  ! {caminho}: {str(e)[:80]}")
            ok = False

    print("\n" + ("Descrições publicadas." if ok else
                  "ATENÇÃO: algo não confere. Vê o resguardo."))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
