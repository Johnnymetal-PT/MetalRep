import argparse
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

XML_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main", "a": "http://schemas.openxmlformats.org/drawingml/2006/main"}


def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    return "\n".join(lines).strip() + "\n"


def _write_lf(path: Path, content: str) -> None:
    """Escreve texto UTF-8 com LF, independentemente do sistema operativo."""
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def _read_text_file(path: Path) -> str:
    data = path.read_bytes()
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1", errors="replace")


def _extract_docx(path: Path) -> str:
    with zipfile.ZipFile(path, "r") as zf:
        xml = zf.read("word/document.xml")
    root = ET.fromstring(xml)
    paragraphs = []
    for p in root.findall(".//w:p", XML_NS):
        chunks = []
        for t in p.findall(".//w:t", XML_NS):
            chunks.append(t.text or "")
        line = "".join(chunks).strip()
        if line:
            paragraphs.append(line)
    return "\n\n".join(paragraphs)


def _extract_pptx(path: Path) -> str:
    slides = []
    with zipfile.ZipFile(path, "r") as zf:
        names = sorted([n for n in zf.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")])
        for name in names:
            root = ET.fromstring(zf.read(name))
            texts = [t.text.strip() for t in root.findall(".//a:t", XML_NS) if t.text and t.text.strip()]
            if texts:
                slides.append("\n".join(texts))
    return "\n\n---\n\n".join(slides)


def _extract_xlsx(path: Path) -> str:
    with zipfile.ZipFile(path, "r") as zf:
        shared = []
        if "xl/sharedStrings.xml" in zf.namelist():
            sroot = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in sroot.findall(".//{*}si"):
                pieces = [t.text or "" for t in si.findall(".//{*}t")]
                shared.append("".join(pieces))

        out_lines = []
        sheet_names = sorted([n for n in zf.namelist() if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")])
        for sheet_name in sheet_names:
            out_lines.append(f"# {sheet_name}")
            sroot = ET.fromstring(zf.read(sheet_name))
            for row in sroot.findall(".//{*}row"):
                cells = []
                for c in row.findall("{*}c"):
                    ref = c.attrib.get("r", "")
                    ctype = c.attrib.get("t")
                    v = c.find("{*}v")
                    value = ""
                    if v is not None and v.text is not None:
                        if ctype == "s":
                            idx = int(v.text)
                            value = shared[idx] if 0 <= idx < len(shared) else ""
                        else:
                            value = v.text
                    if value:
                        cells.append(f"{ref}: {value}")
                if cells:
                    out_lines.append(" | ".join(cells))
            out_lines.append("")
    return "\n".join(out_lines).strip()


def _extract_pdf_fallback(path: Path) -> str:
    data = path.read_bytes().decode("latin-1", errors="ignore")
    chunks = re.findall(r"[A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9\s,.;:()\-_/]{20,}", data)
    unique = []
    seen = set()
    for chunk in chunks:
        c = re.sub(r"\s+", " ", chunk).strip()
        if c and c not in seen:
            seen.add(c)
            unique.append(c)
    if not unique:
        return "[PDF extraction fallback] No readable text extracted with stdlib parser."
    return "\n".join(unique[:300])


def extract_text(path: Path) -> str | None:
    """Texto do anexo, ou None quando o tipo nao e extraivel.

    None significa "nao emitir ficheiros de extraccao". Antes devolvia-se um aviso
    ("[Binary attachment] ...") que era escrito como .md e .txt, o que gerava pares
    de ficheiros identicos e sem informacao para cada .py, .png ou download
    incompleto que estivesse anexado -- 8 copias do mesmo aviso no ultimo pull, todas
    propagadas para cada repo de cliente pelo sync de assets partilhados.

    O consumidor (pg_pull_doc_templates.ps1) ja trata a ausencia de extraccao,
    escrevendo null em extracted_txt/extracted_md no MANIFEST.
    """
    ext = path.suffix.lower()
    if ext == ".docx":
        return _extract_docx(path)
    if ext == ".pptx":
        return _extract_pptx(path)
    if ext == ".xlsx":
        return _extract_xlsx(path)
    if ext in {".txt", ".md", ".csv", ".json", ".xml", ".yml", ".yaml"}:
        return _read_text_file(path)
    # Codigo (.py/.ps1/.sql) fica de fora de proposito. A camada de extraccao existe
    # para dar aos agentes o CONTEUDO de documentos binarios (docx/pptx/xlsx/pdf);
    # um script anexo ja se le no proprio ficheiro, e extrai-lo so criava uma copia
    # byte-a-byte do mesmo conteudo noutro caminho.
    if ext in {".py", ".ps1", ".sql"}:
        return None
    if ext == ".pdf":
        return _extract_pdf_fallback(path)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract doc template asset attachments to text and markdown files.")
    parser.add_argument("--assets-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    assets_dir = Path(args.assets_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    skipped = []
    for asset_path in sorted([p for p in assets_dir.glob("*") if p.is_file()]):
        extracted = extract_text(asset_path)
        if extracted is None:
            skipped.append(asset_path.name)
            continue
        normalized = _normalize_text(extracted)

        txt_name = f"{asset_path.name}.txt"
        md_name = f"{asset_path.name}.md"
        txt_path = output_dir / txt_name
        md_path = output_dir / md_name

        # newline="\n" e obrigatorio: em Windows o modo texto do Python traduz "\n" para
        # "\r\n", e estes ficheiros sao .md/.txt versionados sob "text eol=lf" no
        # .gitattributes. Sem isto, cada pull reescrevia os 80 ficheiros de
        # assets_extracted/ em CRLF e deixava a arvore do framework suja em cada
        # onboarding, sem uma unica linha de conteudo alterada.
        _write_lf(txt_path, normalized)
        _write_lf(md_path, f"# Extracted: {asset_path.name}\n\n{normalized}")

        results.append(
            {
                "asset_name": asset_path.name,
                "txt_file": txt_name,
                "md_file": md_name,
            }
        )

    print(json.dumps({"extracted_assets": results, "skipped_assets": skipped}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())