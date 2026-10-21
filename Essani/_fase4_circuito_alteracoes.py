#!/usr/bin/env python3
"""
Fase 4 (R5) — circuito de alterações de especificação (Essani, produção).

Requisito: quando o vendedor e o cliente acordam uma mudança nas especificações
de um protótipo, essa mudança tem de chegar ao gestor de projeto que gere a
produção — de forma rastreável, e não por email solto.

Como fica: uma regra de automatização sobre `product.template`, disparada só
quando o campo das especificações (`product_properties`) é escrito e só em
artigos da árvore de categorias de protótipos. A ação percorre os projetos
ligados ao artigo pelo campo `x_pg_artigo_prototipo` e, em cada um:
  - regista uma nota no chatter do projeto com as especificações pedidas atuais;
  - agenda uma atividade para o gestor de projeto.

Porque não há risco de ciclo: a ação escreve em `project.project`, nunca no
`product.template` que a disparou.

Porque o filtro por categoria: sem ele a regra seria avaliada em cada escrita de
qualquer um dos 732 artigos do catálogo, para no fim não encontrar projeto nenhum.

Idempotente. Dry-run por defeito; escrita exige --confirm e --allow-prod.
"""
import argparse, sys
sys.path.insert(0, "/Users/laracunha/Documents/Parametro/_pg_template/scripts")
from pg_odoo_migration_guard import Guard, resolver_alvo, resolver_alvo_por_projeto

PROJECT_KEY = "web-essani-intranet-extranet"
NOME_REGRA = "PG Protótipos: alteração de especificações → gestor de projeto"

# O codigo da acao vive num sitio so: no script das correcoes, que carrega a versao
# canonica. Ter uma copia aqui foi o que fez a regra nascer com a v1 defeituosa e
# obrigar a corrigi-la logo a seguir.
from _fase4_corrige_acao import CODIGO, MARCADOR


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

    # Pre-condicoes: o campo de ligacao tem de existir, senao o codigo rebenta em runtime.
    lig = kw("ir.model.fields", "search_count",
             [[["model", "=", "project.project"], ["name", "=", "x_pg_artigo_prototipo"]]])
    if not lig:
        print("ABORTADO: falta o campo x_pg_artigo_prototipo em project.project.")
        return

    cat = kw("product.category", "search_read",
             [[["name", "=", "Protótipos"], ["parent_id", "=", False]], ["id", "complete_name"]])
    if not cat:
        print("ABORTADO: categoria 'Protótipos' não encontrada.")
        return
    cat_id = cat[0]["id"]
    modelo_id = kw("ir.model", "search_read",
                   [[["model", "=", "product.template"]], ["id"]])[0]["id"]
    campo_id = kw("ir.model.fields", "search_read",
                  [[["model", "=", "product.template"],
                    ["name", "=", "product_properties"]], ["id"]])[0]["id"]
    dominio = "[('categ_id', 'child_of', %d)]" % cat_id

    print("=== regra de automatização ===")
    print("  modelo   : product.template")
    print("  disparo  : on_write, só quando 'product_properties' é escrito")
    print("  filtro   : %s   (%s)" % (dominio, cat[0]["complete_name"]))
    print("  ação     : nota no chatter do projeto + atividade para o gestor")

    ja = kw("base.automation", "search_read", [[["name", "=", NOME_REGRA]], ["id", "active"]],
            {"context": {"active_test": False}})
    if ja:
        print("\n  = já existe: id=%s activa=%s" % (ja[0]["id"], ja[0]["active"]))
        # Existir nao chega: a acao pode estar numa versao antiga do codigo.
        r = kw("base.automation", "read", [[ja[0]["id"]], ["action_server_ids"]])[0]
        if not r["action_server_ids"]:
            print("    AVISO: a regra não tem ação associada.")
            return
        aid = r["action_server_ids"][0]
        atual = kw("ir.actions.server", "read", [[aid], ["code"]])[0]["code"] or ""
        if MARCADOR in atual:
            print("    ação id=%s já na versão canónica — nada a fazer." % aid)
        else:
            print("    * ação id=%s está desatualizada — a repor a versão canónica" % aid)
            if escrever:
                kw("ir.actions.server", "write", [[aid], {"code": CODIGO}], allow_write=True)
                v = kw("ir.actions.server", "read", [[aid], ["code"]])[0]["code"]
                print("    reconciliação: versão canónica presente = %s" % (MARCADOR in v))
        return
    print("\n  * a criar")
    if not escrever:
        return

    rid = kw("base.automation", "create", [{
        "name": NOME_REGRA,
        "model_id": modelo_id,
        "trigger": "on_write",
        "trigger_field_ids": [(6, 0, [campo_id])],
        "filter_domain": dominio,
        "active": True,
    }], allow_write=True)
    print("    regra criada id=%s" % rid)

    aid = kw("ir.actions.server", "create", [{
        "name": "Avisar gestor de projeto da alteração de especificações",
        "model_id": modelo_id,
        "state": "code",
        "code": CODIGO,
        "base_automation_id": rid,
        "usage": "base_automation",
    }], allow_write=True)
    print("    ação criada id=%s" % aid)

    v = kw("base.automation", "read", [[rid],
          ["name", "trigger", "filter_domain", "action_server_ids", "active"]])[0]
    print("\n  reconciliação: trigger=%s | ações=%d | activa=%s"
          % (v["trigger"], len(v["action_server_ids"]), v["active"]))


if __name__ == "__main__":
    main()
