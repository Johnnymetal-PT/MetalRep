#!/usr/bin/env python3
"""
Fase 3 — ligação entre o protótipo-projeto e o protótipo-artigo (Essani, produção).

Cria dois campos manuais em `project.project` e a vista herdada que os mostra:

  x_pg_artigo_prototipo  many2one -> product.template   "Artigo do protótipo"
  x_pg_versao_origem     many2one -> project.project    "Versão de origem"

O primeiro liga o projeto ao artigo onde vivem as especificações; o segundo é a
árvore de versões, que substitui o versionamento feito no nome do projeto.

RESSALVA CONSCIENTE: por serem criados por API e não pelo Studio, estes campos
ficam fora do módulo `studio_customization`, ao contrário dos 19 campos manuais
que essa via já registou nesta base. Funcionam de igual modo, mas não viajam numa
exportação do Studio. Foi decisão explícita, com a alternativa (criar à mão no
Studio) posta em cima da mesa primeiro.

REDE DE SEGURANÇA: depois de criar a vista, o script manda o Odoo renderizar o
formulário de projeto. Se a renderização falhar, desativa a vista que acabou de
criar e reporta — uma vista partida deixaria o formulário de projeto inacessível
a toda a gente, e isso não pode depender de alguém reparar a tempo.

Idempotente. Dry-run por defeito; escrita exige --confirm e --allow-prod.
"""
import argparse, sys
sys.path.insert(0, "/Users/laracunha/Documents/Parametro/_pg_template/scripts")
from pg_odoo_migration_guard import Guard, resolver_alvo, resolver_alvo_por_projeto

PROJECT_KEY = "web-essani-intranet-extranet"
MODELO = "project.project"
VISTA_BASE_XMLID = ("project", "edit_project")
NOME_VISTA = "pg.project.prototipo.ligacao"

CAMPOS = [
    {"name": "x_pg_artigo_prototipo", "field_description": "Artigo do protótipo",
     "ttype": "many2one", "relation": "product.template",
     "help": "Artigo de catálogo que representa este protótipo e onde vivem as especificações."},
    {"name": "x_pg_versao_origem", "field_description": "Versão de origem",
     "ttype": "many2one", "relation": "project.project",
     "help": "Protótipo a partir do qual esta versão foi criada. Constrói a árvore de versões."},
]

ARCH = """<data>
  <field name="user_id" position="after">
    <field name="x_pg_artigo_prototipo" options="{'no_create': True}"/>
    <field name="x_pg_versao_origem" options="{'no_create': True}"/>
  </field>
</data>"""


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

    modelo_id = kw("ir.model", "search_read", [[["model", "=", MODELO]], ["id"]])[0]["id"]

    # ---- Op 1: campos ----
    print("=== Op 1: campos em %s ===" % MODELO)
    criar = []
    for c in CAMPOS:
        ex = kw("ir.model.fields", "search_read",
                [[["model", "=", MODELO], ["name", "=", c["name"]]], ["id", "state"]])
        if ex:
            print("  = existe: %s (state=%s)" % (c["name"], ex[0]["state"]))
        else:
            print("  * a criar: %-24s %s -> %s" % (c["name"], c["ttype"], c["relation"]))
            criar.append(c)
    if criar and escrever:
        for c in criar:
            kw("ir.model.fields", "create", [dict(c, model=MODELO, model_id=modelo_id,
                                                  state="manual", on_delete="set null")],
               allow_write=True)
        n = kw("ir.model.fields", "search_count",
               [[["model", "=", MODELO], ["name", "in", [c["name"] for c in CAMPOS]]]])
        print("  reconciliação: %d/%d campos presentes" % (n, len(CAMPOS)))

    # ---- Op 2: vista herdada ----
    print("\n=== Op 2: vista herdada ===")
    ja = kw("ir.ui.view", "search_read", [[["name", "=", NOME_VISTA]], ["id", "active"]],
            {"context": {"active_test": False}})
    if ja:
        print("  = existe: id=%s activa=%s" % (ja[0]["id"], ja[0]["active"]))
    else:
        base = kw("ir.model.data", "search_read",
                  [[["module", "=", VISTA_BASE_XMLID[0]], ["name", "=", VISTA_BASE_XMLID[1]]],
                   ["res_id"]])[0]["res_id"]
        print("  * a criar sobre a vista base id=%s (%s.%s)"
              % (base, VISTA_BASE_XMLID[0], VISTA_BASE_XMLID[1]))
        print("    ancora: <field name='user_id' position='after'>")
        if escrever:
            vid = kw("ir.ui.view", "create", [{
                "name": NOME_VISTA, "model": MODELO, "type": "form",
                "inherit_id": base, "mode": "extension", "priority": 99,
                "arch_db": ARCH,
            }], allow_write=True)
            print("    vista criada id=%s" % vid)

            # rede de seguranca: o formulario ainda renderiza?
            print("\n  verificação de renderização do formulário de projeto...")
            try:
                kw(MODELO, "get_view", [], {"view_type": "form"})
                print("    OK — o formulário renderiza.")
            except Exception as erro:
                print("    FALHOU: %s" % str(erro)[-200:])
                kw("ir.ui.view", "write", [[vid], {"active": False}], allow_write=True)
                print("    vista %s DESATIVADA. Formulário reposto; campos mantidos." % vid)


if __name__ == "__main__":
    main()
