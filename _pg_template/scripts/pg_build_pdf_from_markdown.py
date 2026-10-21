#!/usr/bin/env python3
"""
Gera um PDF com a identidade Parâmetro Global a partir de um documento Markdown.

PORQUE EXISTE
    Os templates executáveis do framework produzem Markdown: é o formato que fica
    versionado, que os agentes leem e que se revê em diff. A framework tinha caminho de
    saída para PPTX, para Word e para HTML colável em email — e não tinha para PDF. Na
    prática, entregar um documento a um cliente era entregar-lhe um `.md` em bruto, ou
    converter à mão.

    Motor: Chromium do Playwright. É um motor de layout a sério, e é o mesmo que serve a
    captura de ecrãs para documentação, pelo que não é uma dependência só para isto.

MAPEAMENTO
    Markdown -> HTML (biblioteca `markdown`, extensões `tables` e `sane_lists`)
    HTML -> PDF (Chromium, `page.pdf()`), com CSS orientado a IMPRESSÃO e não a ecrã.

AS DECISÕES DE PAGINAÇÃO SÃO O QUE FAZ A DIFERENÇA
    `thead { display: table-header-group }` repete o cabeçalho da tabela em cada página.
    Sem isto, uma tabela de 44 linhas parte-se a meio sem cabeçalho e fica inútil — foi
    esse o caso real que deu origem a este conversor, uma folha de classificação de
    artigos para o cliente preencher.
    `table tr { page-break-inside: avoid }` impede uma linha de se partir entre páginas.
    `h2 { page-break-after: avoid }` impede um título de ficar órfão no fim da página.

IDENTIDADE
    A paleta vem de `pg_brand_palette.py`, como no PPTX e no Word. Nenhuma cor é
    escolhida aqui. É essa regra que garante que dois documentos gerados em projetos
    diferentes saem iguais.

Uso:
    py pg_build_pdf_from_markdown.py --input docs/DOC.md --output docs/DOC.pdf
    py pg_build_pdf_from_markdown.py --input docs/DOC.md --subtitulo @sub.txt

Dependências:
    pip install markdown playwright
    python -m playwright install chromium
"""
from __future__ import annotations

import argparse
import io
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pg_brand_palette import (  # noqa: E402
    ACENTO, TINTA, CORPO, SUAVE, CLARO, LINHA, BRANCO, para_css,
)

RODAPE_ENTIDADE = "Parâmetro Global — Consultoria Informática"


def css_do_documento() -> str:
    """CSS de impressão. Todas as cores vêm da paleta da marca."""
    return u"""
@page { size: A4; margin: 18mm 15mm 20mm 15mm; }
* { box-sizing: border-box; }
body {
  font-family: "Aptos", "Segoe UI", "Calibri", system-ui, sans-serif;
  font-size: 10pt; line-height: 1.45; color: %(tinta)s; margin: 0;
}
h1 {
  font-size: 18pt; margin: 0 0 2mm 0; color: %(tinta)s;
  border-bottom: 2px solid %(acento)s; padding-bottom: 2mm;
}
h2 {
  font-size: 12.5pt; margin: 7mm 0 2mm 0; color: %(acento)s;
  /* um titulo nunca fica orfao no fim da pagina */
  page-break-after: avoid;
}
h3 { font-size: 11pt; margin: 5mm 0 1.5mm 0; color: %(tinta)s; page-break-after: avoid; }
p { margin: 0 0 2.5mm 0; }
ul, ol { margin: 0 0 3mm 0; padding-left: 6mm; }
li { margin-bottom: 1mm; }
blockquote {
  margin: 0 0 3mm 0; padding: 1.5mm 3mm; border-left: 1mm solid %(acento)s;
  background: %(claro)s; color: %(corpo)s;
}
code {
  font-family: "Consolas", "Courier New", monospace; font-size: 9.5pt;
  background: %(claro)s; padding: 0.3mm 1.2mm; border-radius: 1mm;
}
pre { background: %(claro)s; padding: 2mm 3mm; border-radius: 1mm; overflow-x: auto; }
pre code { background: none; padding: 0; }
strong { color: %(tinta)s; }
table {
  width: 100%%; border-collapse: collapse; margin: 0 0 4mm 0; font-size: 9pt;
}
th {
  background: %(acento)s; color: %(branco)s; text-align: left; font-weight: 600;
  padding: 1.6mm 2mm; border: 0.3mm solid %(acento)s;
}
td { padding: 1.3mm 2mm; border: 0.3mm solid %(linha)s; vertical-align: top; }
tr:nth-child(even) td { background: %(claro)s; }
/* uma linha de tabela nunca se parte entre paginas */
table tr { page-break-inside: avoid; }
/* e o cabecalho repete-se em cada pagina: sem isto uma tabela longa fica ilegivel */
thead { display: table-header-group; }
.pg-subtitulo { color: %(suave)s; font-size: 9pt; margin: 0 0 5mm 0; }
""" % {
        "tinta": para_css(TINTA),
        "acento": para_css(ACENTO),
        "corpo": para_css(CORPO),
        "suave": para_css(SUAVE),
        "claro": para_css(CLARO),
        "linha": para_css(LINHA),
        "branco": para_css(BRANCO),
    }


def rodape_html() -> str:
    return (u"<div style=\"width:100%%;font-size:7.5pt;color:%s;"
            u"font-family:'Aptos','Segoe UI',sans-serif;padding:0 15mm;"
            u"display:flex;justify-content:space-between;\">"
            u"<span>%s</span>"
            u"<span><span class='pageNumber'></span>/<span class='totalPages'></span></span>"
            u"</div>" % (para_css(SUAVE), RODAPE_ENTIDADE))


def ler_subtitulo(valor: str) -> str:
    """
    Aceita texto directo ou '@ficheiro'.

    O '@ficheiro' não é capricho: passar texto acentuado por argumentos de linha de
    comando em Windows perde os acentos. Um PDF real saiu com «Mobiliario» em vez de
    «Mobiliário», e só se apanhou por inspeção. Ler de um ficheiro UTF-8 resolve.
    """
    if not valor:
        return u""
    if valor.startswith("@"):
        caminho = valor[1:]
        if not os.path.exists(caminho):
            raise SystemExit("Ficheiro de subtitulo nao encontrado: %s" % caminho)
        with io.open(caminho, encoding="utf-8") as fh:
            return fh.read().strip()
    return valor


def construir_html(markdown_texto: str, subtitulo: str) -> str:
    try:
        import markdown as _markdown
    except ImportError:
        raise SystemExit(
            "Falta a biblioteca 'markdown'. Instalar com:  pip install -r requirements.txt")

    corpo = _markdown.markdown(markdown_texto, extensions=["tables", "sane_lists"])
    sub = (u"<p class='pg-subtitulo'>%s</p>" % subtitulo) if subtitulo else u""
    return (u"<!doctype html><html lang='pt-PT'><head><meta charset='utf-8'>"
            u"<style>%s</style></head><body>%s%s</body></html>"
            % (css_do_documento(), sub, corpo))


def escrever_pdf(html: str, destino: Path) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit(
            "Falta o 'playwright'. Instalar com:\n"
            "  pip install -r requirements.txt\n"
            "  python -m playwright install chromium")

    # Absoluto antes de tudo: o temporario herda o caminho do destino, e
    # `Path.as_uri()` recusa caminhos relativos ("relative path can't be expressed as
    # a file URI"). Com `--output docs/x.pdf` o conversor rebentava (issue #63).
    destino = Path(destino).resolve()
    temporario = destino.with_suffix(".pg_tmp.html")
    # Fechar o ficheiro e obrigatorio, nao higiene: em Windows o unlink do finally
    # falha enquanto houver um handle aberto sobre ele.
    with io.open(temporario, "w", encoding="utf-8") as fh:
        fh.write(html)
    try:
        with sync_playwright() as p:
            try:
                navegador = p.chromium.launch()
            except Exception as erro:
                # Falhar aqui em silencio, ou com o traceback do Playwright, e o modo de
                # falha que esta framework mais paga: quem apanha isto tem de saber o
                # comando exacto que resolve.
                raise SystemExit(
                    "Chromium do Playwright nao esta instalado nesta maquina.\n"
                    "  Resolver com:  python -m playwright install chromium\n"
                    "  (detalhe: %s)" % erro)
            pagina = navegador.new_page()
            pagina.goto(temporario.as_uri(), wait_until="load")
            pagina.emulate_media(media="print")
            pagina.pdf(path=str(destino), format="A4", print_background=True,
                       display_header_footer=True,
                       header_template=u"<div></div>", footer_template=rodape_html(),
                       margin={"top": "16mm", "bottom": "18mm",
                               "left": "0mm", "right": "0mm"})
            navegador.close()
    finally:
        if temporario.exists():
            temporario.unlink()


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Markdown -> PDF com a identidade Parametro Global.")
    ap.add_argument("--input", required=True, help="Documento Markdown de origem.")
    ap.add_argument("--output", help="Destino .pdf (por omissao, o mesmo nome do input).")
    ap.add_argument("--subtitulo", default="",
                    help="Subtitulo do documento. Aceita '@ficheiro' para texto acentuado.")
    args = ap.parse_args()

    origem = Path(args.input)
    if not origem.exists():
        raise SystemExit("Documento nao encontrado: %s" % origem)

    destino = Path(args.output) if args.output else origem.with_suffix(".pdf")
    destino.parent.mkdir(parents=True, exist_ok=True)

    with io.open(origem, encoding="utf-8") as fh:
        texto = fh.read()
    html = construir_html(texto, ler_subtitulo(args.subtitulo))
    escrever_pdf(html, destino)

    kb = destino.stat().st_size // 1024
    print("OK: %s (%d KB)" % (destino, kb))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
