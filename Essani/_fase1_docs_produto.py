#!/usr/bin/env python3
"""
Fase 1 - passos rapidos sobre documentos de produto (Essani, producao).

Op A  despublica do website os ficheiros CAD/3D visiveis em produtos publicados.
Op B  poe as fichas tecnicas (PDF) a anexar automaticamente aos orcamentos.

Idempotente: o dominio de cada operacao exclui o estado alvo, por isso correr
duas vezes nao altera nada na segunda. Dry-run por defeito.
"""
import argparse, collections, re, sys, unicodedata
sys.path.insert(0, "/Users/laracunha/Documents/Parametro/_pg_template/scripts")
from pg_odoo_migration_guard import Guard, resolver_alvo, resolver_alvo_por_projeto

PROJECT_KEY = "web-essani-intranet-extranet"
CAD = ["image/vnd.dxf", "application/octet-stream", "model/step", "image/vnd.dwg"]

def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).upper()

def e_ficha_tecnica(nome):
    n = norm(nome)
    if "CERTIFIC" in n or "CONFORMIDADE" in n or re.search(r"\bCE[_ .]", n):
        return False                      # certificado: fica de fora desta passagem
    return "FICHA" in n or "TECNIC" in n or "DATASHEET" in n

def ler_resiliente(kw, ids, campos):
    """read() rebenta se algum registo do lote for inacessivel; bissecta para isolar."""
    out, bloqueados = [], []
    def pega(ch):
        if not ch: return
        try: out.extend(kw("product.document", "read", [ch, campos]))
        except Exception:
            if len(ch) == 1: bloqueados.append(ch[0]); return
            h = len(ch) // 2; pega(ch[:h]); pega(ch[h:])
    for i in range(0, len(ids), 300): pega(ids[i:i+300])
    return out, bloqueados

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--confirm", action="store_true")
    p.add_argument("--allow-prod", action="store_true")
    p.add_argument("--conn", help="ficheiro de ligacao a usar em vez do canal "
                                   "Brodoo; serve para apontar a staging")
    a = p.parse_args()

    alvo = resolver_alvo(a.conn) if a.conn else resolver_alvo_por_projeto(
        PROJECT_KEY, "production")
    g = Guard(alvo, confirmed=a.confirm, allow_prod=a.allow_prod)
    kw = g.kw
    escrever = a.confirm and (a.allow_prod or alvo.purpose != "production")
    print(f"alvo: {alvo.base_url} | base={alvo.database} | finalidade={alvo.purpose}")
    print(f"modo: {'ESCRITA' if escrever else 'DRY-RUN'}\n")

    # ---- Op A ----
    tmpl_pub = kw("product.template", "search", [[["is_published", "=", True]]])
    # Os .max (fonte 3ds Max) chegam com mimetype 'application/x-ole-storage', o mesmo
    # dos .doc/.xls antigos — por isso apanham-se pelo nome, para nao arrastar documentos
    # Office legitimos que partilham o mesmo mimetype.
    domA = [["res_model", "=", "product.template"], ["res_id", "in", tmpl_pub],
            ["shown_on_product_page", "=", True],
            "|", ["mimetype", "in", CAD], ["name", "=like", "%.max"]]
    idsA = kw("product.document", "search", [domA])
    print(f"Op A  CAD/3D visiveis em produtos publicados: {len(idsA)}")
    if idsA and escrever:
        kw("product.document", "write", [idsA, {"shown_on_product_page": False}], allow_write=True)
        print(f"      reconciliacao: restam {kw('product.document','search_count',[domA])} (esperado 0)")

    # ---- Op B ----
    var = kw("product.product", "search", [["|", ["active","=",True], ["active","=",False]]])
    base = ["|", "&", ["res_model","=","product.template"], ["res_id","!=",False],
            "&", ["res_model","=","product.product"], ["res_id","in",var]]
    domB = [["mimetype","=","application/pdf"], ["attached_on_sale","=","hidden"]] + base
    idsB = kw("product.document", "search", [domB])
    recs, bloq = ler_resiliente(kw, idsB, ["name"])
    fichas = [r["id"] for r in recs if e_ficha_tecnica(r["name"])]
    print(f"Op B  PDFs 'hidden' em produtos vivos: {len(idsB)} (inacessiveis: {len(bloq)})")
    print(f"      dos quais fichas tecnicas: {len(fichas)}")
    print(f"      certificados/outros deixados como estao: {len(recs) - len(fichas)}")
    if fichas and escrever:
        for i in range(0, len(fichas), 500):
            kw("product.document", "write",
               [fichas[i:i+500], {"attached_on_sale": "quotation"}], allow_write=True)
        rest = kw("product.document", "search_count",
                  [[["id","in",fichas], ["attached_on_sale","=","hidden"]]])
        ok = kw("product.document", "search_count",
                [[["id","in",fichas], ["attached_on_sale","=","quotation"]]])
        print(f"      reconciliacao: em 'quotation' = {ok}/{len(fichas)} | ainda 'hidden' = {rest} (esperado 0)")

if __name__ == "__main__":
    main()
