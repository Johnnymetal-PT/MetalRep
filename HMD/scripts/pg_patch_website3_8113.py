"""Aplica os cinco patches autorizados da tarefa 8113, com plano e backup.

Corre primeiro sem flags. A aplicação exige --plan, --confirm e --allow-prod.
As alterações limitam-se ao arch_db das cópias do website 3. Não faz upgrade.
"""

import argparse
import datetime as dt
import difflib
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".pg_framework/scripts"))
from pg_odoo_migration_guard import Guard, resolver_alvo_por_projeto

TARGETS = {
    6814: "theme_hmd_furniture.page_portfolio",
    6811: "theme_hmd_furniture.page_fabrics",
    6812: "theme_hmd_furniture.page_materials",
    6810: "theme_hmd_furniture.page_contact_hmd",
    6806: "theme_hmd_furniture.footer_hmd",
}
CONTEXT = {"lang": "en_US", "website_id": 3, "active_test": False}
FIELDS = ["name", "key", "website_id", "active", "arch_db", "write_date"]


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def patch(view_id, old):
    """Altera apenas os fragmentos previstos; uma segunda passagem é neutra."""
    if view_id == 6814:
        expression = r'<figure class="hmd-band" t-foreach="\[1, 2, 3\]" t-as="i">.*?</figure>'
        matches = list(re.finditer(expression, old, re.S))
        if not matches:
            tree = ET.fromstring(old)
            figures = [n for n in tree.iter("figure") if n.get("class") == "hmd-band"]
            if len(figures) == 3 and all("t-foreach" not in n.attrib for n in figures):
                return old
            raise ValueError("Portfolio: estrutura inesperada")
        if len(matches) != 1:
            raise ValueError("Portfolio: loop não é único")
        match = matches[0]
        expected = 't-attf-src="/theme_hmd_furniture/static/src/img/portfolio_0#{i}.jpg"'
        if expected not in match[0]:
            raise ValueError("Portfolio: imagens alteradas; rever o plano")
        # Expande o fragmento original, preservando atributos e formatação.
        figures = []
        for number in range(1, 4):
            figure = match[0].replace(' t-foreach="[1, 2, 3]" t-as="i"', "")
            figure = figure.replace("t-attf-src=", "src=").replace("t-attf-alt=", "alt=")
            figures.append(figure.replace("#{i}", str(number)))
        return old[:match.start()] + "\n                    ".join(figures) + old[match.end():]
    if view_id in (6811, 6812):
        key = "fabrics" if view_id == 6811 else "materials"
        ids = [f"oe_structure_hmd_{key}_{number}" for number in (1, 2)]
        tree = ET.fromstring(old)
        found = [n.get("id") for n in tree.iter() if n.get("id") in ids]
        if len(found) == 2 and set(found) == set(ids):
            return old
        if found:
            raise ValueError(f"{key}: zonas parcialmente aplicadas")
        marker = f'<section class="hmd-bands hmd-bands--{key}">'
        if old.count(marker) != 1:
            raise ValueError(f"{key}: bloco dinâmico não é único")
        start = old.index(marker)
        line_start = old.rfind("\n", 0, start) + 1
        indent = old[line_start:start]
        before = f'{indent}<div id="{ids[0]}" class="oe_structure"/>\n'
        new = old[:line_start] + before + old[line_start:]
        ending = re.search(r'\n(\s*)</div>\s*</t>\s*</t>\s*$', new[new.index(marker):])
        if not ending:
            raise ValueError(f"{key}: fim do wrap não encontrado")
        position = new.index(marker) + ending.start()
        after = f'\n{indent}<div id="{ids[1]}" class="oe_structure"/>'
        return new[:position] + after + new[position:]
    if view_id == 6810:
        expression = r'[ \t]*<input type="hidden" name="csrf_token" t-att-value="request\.csrf_token\(\)"/>\r?\n'
        count = len(re.findall(expression, old))
        if count == 0:
            return old
        if count != 2:
            raise ValueError("Contacto: número de tokens diferente dos dois previstos")
        return re.sub(expression, "", old)
    if view_id == 6806:
        if old.count(' t-ignore="true"') > 1:
            raise ValueError("Rodapé: t-ignore não é único")
        return old.replace(' t-ignore="true"', "")
    raise ValueError("Vista fora do âmbito")


def read_views(guard):
    rows = guard.kw("ir.ui.view", "read", [list(TARGETS)],
                    {"fields": FIELDS, "context": CONTEXT})
    if len(rows) != len(TARGETS):
        raise ValueError("Não foram encontradas as cinco vistas")
    for row in rows:
        if row["key"] != TARGETS[row["id"]] or row["website_id"][0] != 3 or not row["active"]:
            raise ValueError(f"Destino inesperado: {row['id']}")
    return {row["id"]: row for row in rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--allow-prod", action="store_true")
    args = parser.parse_args()
    if args.confirm and (not args.plan or not args.allow_prod):
        parser.error("Aplicar exige --plan e --allow-prod")
    guard = Guard(resolver_alvo_por_projeto("odoo-hmd", "production"),
                  confirmed=args.confirm, allow_prod=args.allow_prod,
                  log_path=str(ROOT / ".pg/migration/api_calls.log.jsonl"))
    base = guard.kw("ir.module.module", "search_read", [[["name", "=", "base"]]],
                    {"fields": ["installed_version"]})
    if not base[0]["installed_version"].startswith("18.0."):
        raise ValueError("A série do destino não é Odoo 18")
    rows = read_views(guard)
    if not args.confirm:
        folder = ROOT / "data_local" / ("w3_8113_" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
        folder.mkdir(parents=True)
        plan = {"website_id": 3, "database": guard.alvo.database,
                "base_url": guard.alvo.base_url, "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "authorization": "Utilizador autorizou retomar os cinco patches em produção neste chat, 13/10/2026.",
                "views": []}
        for view_id in TARGETS:
            row = rows[view_id]
            old = row["arch_db"]
            new = patch(view_id, old)
            ET.fromstring(new)
            if patch(view_id, new) != new:
                raise ValueError(f"Patch não é idempotente: {view_id}")
            if len(new) < len(old) - 400:
                raise ValueError(f"Redução excessiva: {view_id}")
            (folder / f"view_{view_id}_before.xml").write_text(old, encoding="utf-8")
            (folder / f"view_{view_id}_after.xml").write_text(new, encoding="utf-8")
            diff = "".join(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                             fromfile=f"{view_id}_before", tofile=f"{view_id}_after"))
            (folder / f"view_{view_id}.diff").write_text(diff, encoding="utf-8")
            plan["views"].append(dict(row, expected=new, before_sha256=digest(old), after_sha256=digest(new)))
            print(f"{view_id} {row['name']}: {len(old)} -> {len(new)}; idempotência OK")
        destination = folder / "plan.json"
        destination.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"PLAN={destination}")
        return
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    if plan["database"] != guard.alvo.database or plan["base_url"] != guard.alvo.base_url:
        raise ValueError("Ligação diferente da utilizada no dry-run")
    if [v["id"] for v in plan["views"]] != list(TARGETS):
        raise ValueError("Plano não cobre exatamente as cinco vistas autorizadas")
    for entry in plan["views"]:
        row = rows[entry["id"]]
        if row["arch_db"] != entry["arch_db"] or row["write_date"] != entry["write_date"]:
            raise ValueError(f"Vista {row['id']} alterada desde o dry-run; não escrever")
        if patch(row["id"], row["arch_db"]) != entry["expected"]:
            raise ValueError("Plano diferente do patch revisto")
    results = []
    for entry in plan["views"]:
        view_id = entry["id"]
        current = read_views(guard)[view_id]
        if current["arch_db"] != entry["arch_db"] or current["write_date"] != entry["write_date"]:
            raise ValueError(f"Edição concorrente da vista {view_id}; interromper")
        if entry["arch_db"] != entry["expected"]:
            outcome = guard.kw("ir.ui.view", "write", [[view_id], {"arch_db": entry["expected"]}],
                               {"context": CONTEXT}, allow_write=True)
            if outcome is not True:
                raise ValueError(f"Retorno inesperado ao escrever {view_id}")
        actual = read_views(guard)[view_id]
        if actual["arch_db"] != entry["expected"]:
            raise ValueError(f"Divergência após escrita: {view_id}")
        results.append({"id": view_id, "name": entry["name"], "sha256": digest(actual["arch_db"]), "verified": True})
        (args.plan.parent / "result.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{view_id} {entry['name']}: aplicado, leitura idêntica ao plano")
    print(f"RECONCILIAÇÃO: {len(plan['views'])} previstas = {len(results)} verificadas; 0 divergências")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
