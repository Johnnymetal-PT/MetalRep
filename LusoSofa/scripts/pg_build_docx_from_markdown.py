#!/usr/bin/env python3
"""
Gera um .docx com a identidade Parâmetro Global a partir de um documento Markdown.

PORQUE EXISTE
    Os templates executáveis do framework (TPL_LEVANTAMENTO_AMBITO,
    TPL_PONTO_SITUACAO, ...) produzem Markdown: é o formato que fica versionado
    no repo, que os agentes leem e que se revê em diff. O que vai para o cliente,
    porém, tem de sair com o layout da marca. Este script faz essa passagem sem
    duplicar o conteúdo em dois sítios.

    A identidade vem toda de pg_docx_identity.py, que por sua vez a herda do
    template oficial. Este script decide apenas o mapeamento Markdown -> componente.

MAPEAMENTO
    # H1        -> capa (o primeiro) / título de secção (os seguintes)
    ## H2       -> subtítulo azul
    ### H3      -> título menor
    - [ ] item  -> checklist
    - item      -> bullet
    | a | b |   -> tabela da marca
    > nota      -> caixa de nota
    ---         -> ignorado (a separação já vem dos títulos)
    **negrito**, *itálico* e `código` são preservados no corpo, listas e tabelas;
    nos títulos são retirados, porque a formatação já vem do componente.
    O bloco de metadados imediatamente a seguir ao H1 (tabela ou linhas `**x:** y`)
    é promovido à capa.

Uso:
    py pg_build_docx_from_markdown.py --input docs/DOC.md --output docs/DOC.docx
    py pg_build_docx_from_markdown.py --input docs/DOC.md --label "Levantamento | 2026"

Dependências:
    pip install python-docx
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pg_docx_identity as identity  # noqa: E402

TABLE_ROW = re.compile(r"^\|(.+)\|\s*$")
TABLE_SEPARATOR = re.compile(r"^\|[\s:|-]+\|\s*$")
CHECKBOX = re.compile(r"^[-*]\s+\[( |x|X)\]\s+(.*)$")
BULLET = re.compile(r"^[-*]\s+(.*)$")
NUMBERED = re.compile(r"^\d+\.\s+(.*)$")


def strip_inline(text: str) -> str:
    """Remove marcação inline.

    Só onde a formatação é imposta pelo componente e não faz sentido variar:
    títulos, que já saem a negrito, e o bloco de metadados da capa. O corpo, as
    listas e as tabelas conservam a marcação — quem a interpreta é o
    identity.add_rich_text.
    """
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text.strip()


def keep_inline(text: str) -> str:
    """Preserva a marcação inline; o componente da identidade é que a interpreta."""
    return text.strip()


def split_row(line: str) -> list[str]:
    return [keep_inline(cell) for cell in line.strip().strip("|").split("|")]


def parse_blocks(lines: list[str]) -> list[dict]:
    blocks: list[dict] = []
    index = 0
    while index < len(lines):
        raw = lines[index]
        line = raw.strip()

        if not line or line in {"---", "***", "___"}:
            index += 1
            continue

        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            blocks.append({"type": f"h{min(level, 3)}", "text": strip_inline(line.lstrip("#").strip())})
            index += 1
            continue

        if TABLE_ROW.match(line):
            rows = []
            while index < len(lines) and TABLE_ROW.match(lines[index].strip()):
                candidate = lines[index].strip()
                if not TABLE_SEPARATOR.match(candidate):
                    rows.append(split_row(candidate))
                index += 1
            if rows:
                blocks.append({"type": "table", "headers": rows[0], "rows": rows[1:]})
            continue

        if line.startswith(">"):
            note = [keep_inline(line.lstrip(">").strip())]
            index += 1
            while index < len(lines) and lines[index].strip().startswith(">"):
                note.append(keep_inline(lines[index].strip().lstrip(">").strip()))
                index += 1
            blocks.append({"type": "note", "text": " ".join(n for n in note if n)})
            continue

        checkbox = CHECKBOX.match(line)
        if checkbox:
            blocks.append({
                "type": "checkbox",
                "checked": checkbox.group(1).lower() == "x",
                "text": keep_inline(checkbox.group(2)),
            })
            index += 1
            continue

        bullet = BULLET.match(line)
        if bullet:
            indent = len(raw) - len(raw.lstrip())
            blocks.append({"type": "bullet", "text": keep_inline(bullet.group(1)), "level": indent // 2})
            index += 1
            continue

        numbered = NUMBERED.match(line)
        if numbered:
            blocks.append({"type": "bullet", "text": keep_inline(numbered.group(1)), "level": 0})
            index += 1
            continue

        blocks.append({"type": "body", "text": keep_inline(line)})
        index += 1

    return blocks


def build(markdown_path: Path, output_path: Path, label: str | None) -> Path:
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    blocks = parse_blocks(lines)
    if not blocks:
        raise ValueError(f"Documento sem conteudo utilizavel: {markdown_path}")

    doc = identity.new_document()

    # Capa: primeiro H1 e, se existir, o bloco de metadados que vem logo a seguir.
    title = "Documento"
    start = 0
    if blocks and blocks[0]["type"] == "h1":
        title = blocks[0]["text"]
        start = 1

    meta_lines: list[str] = []
    if start < len(blocks) and blocks[start]["type"] == "table":
        meta = blocks[start]
        for row in meta["rows"]:
            if len(row) >= 2 and row[0] and row[1]:
                meta_lines.append(f"{strip_inline(row[0])}: {strip_inline(row[1])}")
        start += 1

    subtitle = ""
    if " — " in title:
        title, subtitle = title.split(" — ", 1)

    identity.add_cover(doc, title=title, subtitle=subtitle, meta_lines=meta_lines[:8])
    identity.configure_header_footer(doc.sections[-1], doc_label=label or title)

    # Quando o unico H1 foi para a capa, os H2 sao as seccoes de topo do corpo e
    # sobem um nivel. Sem isto o documento sai todo ao mesmo peso visual.
    body_blocks = blocks[start:]
    promote = not any(b["type"] == "h1" for b in body_blocks)

    for block in body_blocks:
        kind = block["type"]
        if promote and kind in {"h2", "h3"}:
            kind = "h1" if kind == "h2" else "h2"

        if kind == "h1":
            identity.add_section_title(doc, block["text"])
        elif kind == "h2":
            identity.add_subtitle(doc, block["text"])
        elif kind == "h3":
            identity.add_minor_title(doc, block["text"])
        elif kind == "table":
            identity.add_table(doc, block["headers"], block["rows"])
        elif kind == "note":
            identity.add_note(doc, block["text"])
        elif kind == "checkbox":
            identity.add_checkbox(doc, block["text"], checked=block["checked"])
        elif kind == "bullet":
            identity.add_bullet(doc, block["text"], level=block.get("level", 0))
        elif block["text"]:
            identity.add_body(doc, block["text"])

    return identity.save(doc, output_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera um .docx da marca a partir de Markdown.")
    parser.add_argument("--input", required=True, help="Documento Markdown de origem.")
    parser.add_argument("--output", help="Destino .docx (por omissao, o mesmo nome do input).")
    parser.add_argument("--label", help="Rotulo do rodape (por omissao, o titulo do documento).")
    args = parser.parse_args()

    markdown_path = Path(args.input)
    if not markdown_path.exists():
        print(f"ERRO: ficheiro nao encontrado: {markdown_path}", file=sys.stderr)
        return 1

    output_path = Path(args.output) if args.output else markdown_path.with_suffix(".docx")
    result = build(markdown_path, output_path, args.label)
    print(f"OK: documento gerado em {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
