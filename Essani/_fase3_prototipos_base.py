#!/usr/bin/env python3
"""
Fase 3 (base) — estrutura de protótipos (Essani, produção).

Op 1  Árvore de categorias de produto para protótipos.
Op 2  Especificações por categoria, em `product.category.product_properties_definition`.
      É este o mecanismo certo no Odoo 19: as Properties do produto são definidas na
      categoria e preenchidas em cada artigo (`product.template.product_properties`).
      Atributos de produto NÃO servem: os sete usados nesta família estão todos em
      `create_variant='always'` e cada especificação geraria variantes.
Op 3  Sequência das referências internas de protótipo (PROT-AAAA-NNNN).

As especificações da categoria-piloto saem dos atributos realmente usados nos 31
artigos de Transformadores: Load capacity (29), Output (26), Input (17), Voltage,
IP, Amps e Power. Os valores de IP são lidos da base, não inventados.

Idempotente. Dry-run por defeito; escrita exige --confirm e --allow-prod.
"""
import argparse, sys
sys.path.insert(0, "/Users/laracunha/Documents/Parametro/_pg_template/scripts")
from pg_odoo_migration_guard import Guard, resolver_alvo, resolver_alvo_por_projeto

PROJECT_KEY = "web-essani-intranet-extranet"
CAT_RAIZ, CAT_PILOTO = "Protótipos", "Fontes de alimentação"
SEQ_CODE = "pg.prototipo.ref"


def definicao_specs(ips):
    """Pedidas no início, finais no fim — a ordem em que aparecem no artigo."""
    nucleo = [
        ("tensao_entrada",   "Tensão de entrada",   "char",      None),
        ("tensao_saida",     "Tensão de saída",     "char",      None),
        ("potencia_w",       "Potência (W)",        "float",     None),
        ("corrente_max_a",   "Corrente máxima (A)", "float",     None),
        ("capacidade_carga", "Capacidade de carga", "char",      None),
        ("grau_ip",          "Grau de proteção IP", "selection", ips),
    ]
    d = [{"name": "sep_pedidas", "type": "separator", "string": "Especificações pedidas"}]
    for n, s, t, sel in nucleo:
        c = {"name": "req_" + n, "type": t, "string": s}
        if sel:
            c["selection"] = sel
        d.append(c)
    d.append({"name": "req_notas", "type": "char", "string": "Notas do cliente"})
    d.append({"name": "sep_finais", "type": "separator",
              "string": "Especificações finais (validadas)"})
    for n, s, t, sel in nucleo:
        c = {"name": "fin_" + n, "type": t, "string": s}
        if sel:
            c["selection"] = sel
        d.append(c)
    d.append({"name": "fin_desvio", "type": "char", "string": "Desvio face ao pedido"})
    return d


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
    print("alvo: %s | base=%s | finalidade=%s" % (alvo.base_url, alvo.database, alvo.purpose))
    print("modo: %s\n" % ("ESCRITA" if escrever else "DRY-RUN"))

    # ---- Op 1: categorias ----
    print("=== Op 1: categorias de protótipo ===")

    def garante_cat(nome, parent_id):
        dom = [["name", "=", nome]]
        dom.append(["parent_id", "=", parent_id] if parent_id else ["parent_id", "=", False])
        ex = kw("product.category", "search_read", [dom, ["id", "complete_name"]])
        if ex:
            print("  = existe: %s" % ex[0]["complete_name"])
            return ex[0]["id"]
        print("  * a criar: %s (pai=%s)" % (nome, parent_id))
        if not escrever:
            return None
        return kw("product.category", "create",
                  [{"name": nome, "parent_id": parent_id}], allow_write=True)

    raiz = garante_cat(CAT_RAIZ, False)
    piloto = garante_cat(CAT_PILOTO, raiz) if raiz else None

    # ---- Op 2: especificações da categoria-piloto ----
    print("\n=== Op 2: especificações da categoria-piloto ===")
    vals = kw("product.attribute.value", "search_read",
              [[["attribute_id.name", "=", "IP"]], ["name"]])
    ips = sorted({v["name"].strip() for v in vals})
    ips_sel = [[v.lower().replace(" ", "_"), v] for v in ips] or [["ip20", "IP20"]]
    print("  valores de IP lidos da base: %s" % (ips or "(nenhum)"))
    d = definicao_specs(ips_sel)
    print("  entradas na definição: %d" % len(d))
    for e in d:
        marca = "--" if e["type"] == "separator" else "  "
        print("    %s %-42s %s" % (marca, e["string"][:40], e["type"]))
    if piloto:
        atual = kw("product.category", "read", [[piloto], ["product_properties_definition"]])[0]
        n_atual = len(atual.get("product_properties_definition") or [])
        print("  definição atual na categoria: %d entradas" % n_atual)
        if n_atual:
            print("  ABORTADO nesta operação: a categoria já tem definição; não sobrescrevo.")
        elif escrever:
            kw("product.category", "write",
               [[piloto], {"product_properties_definition": d}], allow_write=True)
            v = kw("product.category", "read", [[piloto], ["product_properties_definition"]])[0]
            print("  reconciliação: %d entradas (esperado %d)"
                  % (len(v["product_properties_definition"]), len(d)))

    # ---- Op 3: sequência de referências ----
    print("\n=== Op 3: sequência de referências de protótipo ===")
    ex = kw("ir.sequence", "search_read",
            [[["code", "=", SEQ_CODE]], ["id", "prefix", "number_next_actual"]])
    if ex:
        print("  = existe: %s (próximo=%s)" % (ex[0]["prefix"], ex[0]["number_next_actual"]))
    else:
        print("  * a criar: PROT-%(year)s- , 4 dígitos")
        if escrever:
            sid = kw("ir.sequence", "create", [{
                "name": "PG Referência de protótipo", "code": SEQ_CODE,
                "prefix": "PROT-%(year)s-", "padding": 4, "implementation": "standard",
            }], allow_write=True)
            print("  reconciliação: sequência criada id=%s" % sid)


if __name__ == "__main__":
    main()
