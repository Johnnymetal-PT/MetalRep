#!/usr/bin/env python3
"""
Corrige as traducoes pt_PT (e outras nao-base) do campo `name` dos produtos
promovidos (Staging -> Producao).

CONTEXTO
--------
O `promote_products.py` copiou os campos sem tratar traducoes: leu/escreveu um
unico valor por campo. Como `product.template.name` e traduzivel, na base de
destino as linguas nao-base ficaram com o valor base (en_US) replicado.
Exemplo: test tem en_US "LED Spot30" / pt_PT "LED Spot30 12V DC", mas na main o
pt_PT ficou "LED Spot30".

Este script vai buscar a traducao pt_PT (e quaisquer outras linguas != en_US) na
ORIGEM e reescreve-a no produto CERTO da main. So mexe no campo `name` e NUNCA
escreve a lingua base en_US (que ja foi copiada corretamente). A origem nunca e
escrita.

RESOLUCAO origem -> destino (autoritativa, idempotente):
- SO por external id `__promote__.tmpl_<src_id>` em ir.model.data, criado pelo
  promote para cada template promovido. (Sem fallback por default_code: codigos
  iguais entre produtos distintos -- ex.: 'ph' -- causam falsos positivos.)

SALVAGUARDA
-----------
Para cada par (src, dst) ligado por external id, confirma-se que o `name` en_US
coincide entre as duas bases (o promote copiou-o verbatim). Se diferir, o par e
SALTADO e listado para revisao manual -- nao se arrisca escrever no produto errado.

USO
---
  # Dry-run (nao escreve), gera relatorio UTF-8:
  python scripts/fix_name_translations.py --env scripts/.promote.env

  # Aplicar de facto:
  python scripts/fix_name_translations.py --env scripts/.promote.env --apply
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from promote_products import OdooClient, load_env, setup_logging  # noqa: E402

FIELD = "name"
MODEL = "product.template"
BASE_LANG = "en_US"  # lingua-fonte; nunca e reescrita
DEFAULT_REPORT = str(Path(__file__).resolve().parent / "_fix_name_translations_report.txt")


def read_names_by_lang(client, ids, langs):
    """Devolve {lang: {id: name}} lendo `name` no contexto de cada lingua."""
    out = {}
    for lang in langs:
        rows = client.kw(MODEL, "read", [ids, [FIELD]], {"context": {"lang": lang}})
        out[lang] = {r["id"]: (r.get(FIELD) or "") for r in rows}
    return out


def resolve_pairs(dst, log, only_src_ids=None):
    """(src_tmpl_id -> dst_tmpl_id) a partir dos external ids __promote__.tmpl_*."""
    domain = [("module", "=", "__promote__"),
              ("model", "=", MODEL),
              ("name", "like", "tmpl_%")]
    rows = dst.search_read("ir.model.data", domain, ["name", "res_id"])
    pairs = {}
    for r in rows:
        try:
            src_id = int(r["name"].split("tmpl_", 1)[1])
        except (IndexError, ValueError):
            log.warning(f"  ! external id inesperado: {r['name']} -- ignorado")
            continue
        pairs[src_id] = r["res_id"]
    log.info(f"{len(pairs)} templates resolvidos por external id __promote__.tmpl_*")
    if only_src_ids:
        pairs = {k: v for k, v in pairs.items() if k in only_src_ids}
    return pairs


def main(argv=None):
    ap = argparse.ArgumentParser(description="Corrige traducoes pt_PT do name dos produtos promovidos")
    ap.add_argument("--env", help="ficheiro .env com SRC_*/DST_*")
    ap.add_argument("--src-ids", help="lista de product.template ids da ORIGEM, separada por virgulas")
    ap.add_argument("--apply", action="store_true", help="escreve de facto (default: dry-run)")
    ap.add_argument("--report", default=DEFAULT_REPORT, help="caminho do relatorio UTF-8")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv)

    log = setup_logging(args.verbose)
    load_env(args.env)
    dry = not args.apply

    src = OdooClient(os.environ["SRC_URL"], os.environ["SRC_DB"],
                     os.environ["SRC_LOGIN"], os.environ["SRC_API_KEY"], "SRC", log)
    dst = OdooClient(os.environ["DST_URL"], os.environ["DST_DB"],
                     os.environ["DST_LOGIN"], os.environ["DST_API_KEY"], "DST", log)

    # Linguas a corrigir: ativas comuns a ambas as bases, exceto a base en_US.
    src_langs = {r["code"] for r in src.search_read("res.lang", [("active", "=", True)], ["code"])}
    dst_langs = {r["code"] for r in dst.search_read("res.lang", [("active", "=", True)], ["code"])}
    common = src_langs & dst_langs
    fix_langs = sorted(l for l in common if l != BASE_LANG)
    log.info(f"linguas comuns ativas={sorted(common)} | a corrigir (sem base)={fix_langs}")
    if not fix_langs:
        log.warning("Nao ha linguas nao-base para corrigir.")
        return 0

    only = [int(x) for x in args.src_ids.split(",") if x.strip()] if args.src_ids else None
    pairs = resolve_pairs(dst, log, only_src_ids=only)
    if not pairs:
        log.warning("Nenhum template resolvido por external id. Nada a fazer.")
        return 0

    src_ids = list(pairs.keys())
    dst_ids = [pairs[i] for i in src_ids]
    read_langs = [BASE_LANG] + fix_langs
    src_names = read_names_by_lang(src, src_ids, read_langs)
    dst_names = read_names_by_lang(dst, dst_ids, read_langs)

    changes = []   # (src_id, dst_id, lang, old, new)
    suspects = []  # (src_id, dst_id, src_en, dst_en)
    missing = []
    for s_id in src_ids:
        d_id = pairs[s_id]
        if d_id not in dst_names[BASE_LANG]:
            missing.append((s_id, d_id))
            continue
        src_en = src_names[BASE_LANG].get(s_id, "")
        dst_en = dst_names[BASE_LANG].get(d_id, "")
        if src_en != dst_en:
            suspects.append((s_id, d_id, src_en, dst_en))
            continue
        for lang in fix_langs:
            s_val = src_names[lang].get(s_id, "")
            d_val = dst_names[lang].get(d_id, "")
            if s_val and s_val != d_val:
                changes.append((s_id, d_id, lang, d_val, s_val))

    # Relatorio UTF-8 (evita mojibake da consola Windows).
    lines = []
    lines.append(f"# Correcao traducoes '{FIELD}' (test -> main) | modo={'APPLY' if not dry else 'DRY-RUN'}")
    lines.append(f"# pares por external id: {len(pairs)} | linguas: {fix_langs}")
    lines.append(f"# alteracoes: {len(changes)} | saltados(en_US difere): {len(suspects)} | dst inexistente: {len(missing)}")
    lines.append("")
    lines.append("## ALTERACOES (dst atual -> novo do test)")
    for s_id, d_id, lang, old, new in changes:
        lines.append(f"src#{s_id} -> dst#{d_id} [{lang}]: {old!r} -> {new!r}")
    if suspects:
        lines.append("")
        lines.append("## SALTADOS - en_US difere (revisao manual; NAO alterados)")
        for s_id, d_id, src_en, dst_en in suspects:
            lines.append(f"src#{s_id} -> dst#{d_id}: test.en_US={src_en!r} | main.en_US={dst_en!r}")
    if missing:
        lines.append("")
        lines.append("## DST INEXISTENTE")
        for s_id, d_id in missing:
            lines.append(f"src#{s_id} -> dst#{d_id} (nao encontrado)")
    Path(args.report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    log.info(f"relatorio escrito em {args.report}")

    if not dry:
        for s_id, d_id, lang, old, new in changes:
            dst.kw(MODEL, "write", [[d_id], {FIELD: new}], {"context": {"lang": lang}})
        log.info(f"APLICADO: {len(changes)} traducoes escritas em {len(set(c[1] for c in changes))} templates.")
    else:
        log.info(f"DRY-RUN: {len(changes)} traducoes em {len(set(c[1] for c in changes))} templates (nada escrito).")
    if suspects:
        log.info(f"ATENCAO: {len(suspects)} pares saltados por en_US diferente (ver relatorio).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
