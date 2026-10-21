#!/usr/bin/env python3
"""
Fase 3 — ação "Nova versão do protótipo" (Essani, produção).

Requisito coberto: «se criar um protótipo a partir de uma versão que já existe,
guarda as especificações do produto, as etapas de produção e as tarefas».

Fica como ação de servidor ligada a `project.project`, disponível no menu de
engrenagem (⚙) do formulário do protótipo. Ao correr:
  1. consome a sequência `pg.prototipo.ref` — a referência PROT- passa a ser
     atribuída pelo sistema e deixa de ser escrita à mão;
  2. duplica o artigo, trazendo as especificações da versão anterior;
  3. duplica o projeto, trazendo etapas e tarefas;
  4. liga o projeto novo ao artigo novo e preenche `x_pg_versao_origem`, que é
     o que constrói a árvore de versões;
  5. abre o protótipo novo.

Porque é ação de servidor e não um módulo: vive na base de dados, como a regra
de automatização, e por isso não depende da branch de desenvolvimento por decidir.
Quando o assistente de criação a partir do CRM for escrito como módulo, esta ação
é substituída por ele — e desativa-se, não se apaga.

Nota sobre a duplicação do artigo: `copy()` é uma criação, não uma escrita, pelo
que NÃO dispara a regra 17 (que reage a `write` em `product_properties`). O gestor
não recebe uma notificação espúria por se ter criado uma versão.

Idempotente pelo marcador de versão. Dry-run por defeito; escrita exige --confirm
e --allow-prod.
"""
import argparse, sys
sys.path.insert(0, "/Users/laracunha/Documents/Parametro/_pg_template/scripts")
from pg_odoo_migration_guard import Guard, resolver_alvo, resolver_alvo_por_projeto

PROJECT_KEY = "web-essani-intranet-extranet"
NOME_ACAO = "PG Protótipos: nova versão"
MARCADOR = "# pg-nova-versao v3"

CODIGO = r'''# pg-nova-versao v3
# Cria a versao seguinte de um prototipo, a partir da versao aberta.
for origem in records:
    # Recusar ANTES de consumir a sequencia. Sem esta guarda, correr a acao num
    # projeto qualquer criava uma copia com uma referencia PROT- que nao pertencia
    # a artigo nenhum, e a referencia ficava gasta. Aconteceu no primeiro ensaio.
    artigo = origem.x_pg_artigo_prototipo
    if not artigo:
        raise UserError(
            "O projeto '%s' n\u00e3o \u00e9 um prot\u00f3tipo: n\u00e3o tem "
            "artigo associado.\n\n"
            "Preencha 'Artigo do prot\u00f3tipo' antes de criar uma vers\u00e3o "
            "\u2014 \u00e9 da\u00ed que vem a heran\u00e7a das "
            "especifica\u00e7\u00f5es." % origem.display_name)

    nova_ref = env["ir.sequence"].next_by_code("pg.prototipo.ref")
    if not nova_ref:
        raise UserError("Sequ\u00eancia 'pg.prototipo.ref' n\u00e3o encontrada. "
                        "Sem refer\u00eancia n\u00e3o se cria a vers\u00e3o.")

    # As especificacoes viajam com o artigo: e por isso que a versao nova nasce
    # ja com o que a anterior tinha, em vez de em branco.
    artigo_novo = artigo.copy({"default_code": nova_ref, "name": artigo.name})
    valores = {"x_pg_versao_origem": origem.id,
               "x_pg_artigo_prototipo": artigo_novo.id}

    projeto_novo = origem.copy({"name": "%s [%s]" % (origem.name, nova_ref)})
    projeto_novo.write(valores)

    action = {
        "type": "ir.actions.act_window",
        "name": "Nova vers\u00e3o",
        "res_model": "project.project",
        "res_id": projeto_novo.id,
        "view_mode": "form",
        "target": "current",
    }
'''


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
    print("alvo: %s | base=%s" % (alvo.base_url, alvo.database))
    print("modo: %s\n" % ("ESCRITA" if escrever else "DRY-RUN"))

    # Pre-condicoes: sem estas, a acao rebenta em runtime na cara de quem a usar.
    faltas = []
    if not kw("ir.sequence", "search_count", [[["code", "=", "pg.prototipo.ref"]]]):
        faltas.append("sequência pg.prototipo.ref")
    for campo in ("x_pg_artigo_prototipo", "x_pg_versao_origem"):
        if not kw("ir.model.fields", "search_count",
                  [[["model", "=", "project.project"], ["name", "=", campo]]]):
            faltas.append("campo %s" % campo)
    if faltas:
        print("ABORTADO — em falta: %s" % ", ".join(faltas))
        return
    print("pré-condições: sequência e campos de ligação presentes.")

    # Compilar o codigo que vai ser publicado, e o valor em memoria — nao o texto
    # do ficheiro. Foi essa a distincao que falhou: o texto compilava, mas depois de
    # o Python interpretar os escapes o valor real ja era invalido.
    try:
        compile(CODIGO, "<codigo da acao>", "exec")
        print("sintaxe do código a publicar: OK\n")
    except SyntaxError as erro:
        print("ABORTADO — o código a publicar não compila: %s (linha %s)"
              % (erro.msg, erro.lineno))
        return

    modelo_id = kw("ir.model", "search_read",
                   [[["model", "=", "project.project"]], ["id"]])[0]["id"]

    print("\n=== ação de servidor ===")
    print("  nome     : %s" % NOME_ACAO)
    print("  modelo   : project.project")
    print("  ligação  : menu de engrenagem (⚙) no formulário")
    print("  faz      : sequência -> duplica artigo -> duplica projeto -> liga -> abre")

    ja = kw("ir.actions.server", "search_read", [[["name", "=", NOME_ACAO]], ["id", "code"]])
    if ja:
        atual = ja[0]
        if MARCADOR in (atual["code"] or ""):
            print("\n  = já existe na v1 (id=%s) — nada a fazer." % atual["id"])
            return
        print("\n  * existe (id=%s) mas noutra versão — a substituir o código" % atual["id"])
        if escrever:
            kw("ir.actions.server", "write", [[atual["id"]], {"code": CODIGO}], allow_write=True)
            print("    atualizada.")
        return

    print("\n  * a criar")
    if not escrever:
        return
    aid = kw("ir.actions.server", "create", [{
        "name": NOME_ACAO,
        "model_id": modelo_id,
        "state": "code",
        "code": CODIGO,
        "binding_model_id": modelo_id,
        "binding_view_types": "form",
    }], allow_write=True)
    print("    ação criada id=%s" % aid)
    v = kw("ir.actions.server", "read", [[aid],
          ["name", "state", "binding_model_id", "binding_view_types"]])[0]
    print("    reconciliação: state=%s | ligada a=%s | vistas=%s"
          % (v["state"], v["binding_model_id"][1], v["binding_view_types"]))


if __name__ == "__main__":
    main()
