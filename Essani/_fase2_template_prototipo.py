#!/usr/bin/env python3
"""
Fase 2 - template de projeto para prototipos (Essani, producao).

Op 1  Liga ao projeto-modelo "Produto Novo" o conjunto canonico de etapas de
      engenharia. Reutiliza a etapa existente quando o nome coincide (as etapas
      no Odoo sao partilhaveis entre projetos) e so cria as que faltam, para nao
      multiplicar duplicados como o par "Design"/"Desing".
Op 2  Ativa marcos e dependencias de tarefas nesse projeto. No Odoo 19 estas
      opcoes sao por projeto, nao globais, por isso vivem no template e sao
      herdadas por cada prototipo criado a partir dele.

Idempotente: cada passo verifica o estado antes de escrever.
Dry-run por defeito; escrita exige --confirm e, em producao, --allow-prod.
"""
import argparse, sys
sys.path.insert(0, "/Users/laracunha/Documents/Parametro/_pg_template/scripts")
from pg_odoo_migration_guard import Guard, resolver_alvo, resolver_alvo_por_projeto

PROJECT_KEY = "web-essani-intranet-extranet"
TEMPLATE_ID = 4          # projeto "Produto Novo" (is_template=True, 0 tarefas)

# (nome canonico, sequencia, dobrada no kanban)
ETAPAS = [
    ("Levantamento de requisitos", 10, False),
    ("Estado da Arte",             20, False),
    ("Conceção e design",          30, False),
    ("Desenvolvimento",            40, False),
    ("Amostras",                   50, False),
    ("Testes e validação",         60, False),
    ("Validação de Artigo",        70, False),
    ("Produção",                   80, False),
    ("Concluído",                  90, True),
    ("Recusado",                  100, True),
]

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

    proj = kw("project.project", "read", [[TEMPLATE_ID],
              ["name", "is_template", "allow_milestones", "allow_task_dependencies"]])[0]
    print(f"template alvo: [{TEMPLATE_ID}] {proj['name']} (is_template={proj['is_template']})")
    if not proj["is_template"]:
        print("  ABORTADO: o projeto alvo nao esta marcado como template."); return

    # ---------------- Op 1: etapas ----------------
    # Etapas DEDICADAS ao template, e nao reaproveitamento das existentes.
    # Reutilizar obrigaria a reescrever a sequencia de etapas partilhadas por 9
    # projetos vivos (hoje com sequencias 0-3, sem ordem util), reordenando-lhes o
    # kanban sem que ninguem o tenha pedido. Criadas aqui, ficam com a ordem certa,
    # sem efeito colateral, e cada prototipo criado a partir do template passa a
    # partilhar este mesmo conjunto canonico.
    print("\n=== Op 1: etapas canonicas dedicadas ao template ===")
    atuais = kw("project.task.type", "search_read",
                [[["project_ids", "in", [TEMPLATE_ID]]], ["id", "name"]])
    ja = {e["name"] for e in atuais}
    criar = [(n, s_, f) for n, s_, f in ETAPAS if n not in ja]
    print(f"  ja no template : {len(ja)}  {sorted(ja)}")
    print(f"  a criar        : {len(criar)}")
    for n, s_, f in criar:
        print(f"     * {n:32} seq={s_:<4} dobrada={f}")
    # Etapas que ja estao no template mas nao pertencem ao conjunto canonico.
    # Desligam-se do template (write no project_ids), nunca se apagam: continuam
    # a existir e a servir os projetos que as usam. So e seguro porque o template
    # nao tem tarefas — uma etapa com tarefas ficaria com elas orfas.
    canonicas = {n for n, _, _ in ETAPAS}
    sobram = [e for e in atuais if e["name"] not in canonicas]
    n_tarefas = kw("project.task", "search_count",
                   [[["project_id", "=", TEMPLATE_ID]]], {"context": {"active_test": False}})
    print(f"  a desligar do template : {len(sobram)}  {[e['name'] for e in sobram]}")
    if sobram and n_tarefas:
        print(f"  ABORTADO: o template tem {n_tarefas} tarefas; nao desligo etapas.")
        sobram = []
    if sobram and escrever:
        for e in sobram:
            kw("project.task.type", "write",
               [[e["id"]], {"project_ids": [(3, TEMPLATE_ID)]}], allow_write=True)

    if criar and escrever:
        for nome, seq, fold in criar:
            kw("project.task.type", "create",
               [{"name": nome, "sequence": seq, "fold": fold,
                 "project_ids": [(6, 0, [TEMPLATE_ID])]}], allow_write=True)
        n = kw("project.task.type", "search_count", [[["project_ids", "in", [TEMPLATE_ID]]]])
        print(f"  reconciliacao: etapas no template = {n} (esperado {len(ETAPAS)})")

    # ---------------- Op 2: marcos e dependencias ----------------
    print("\n=== Op 2: marcos e dependencias no template ===")
    faltam = {k: True for k in ("allow_milestones", "allow_task_dependencies")
              if not proj.get(k)}
    print(f"  a ativar: {list(faltam) or 'nada (ja ativos)'}")
    if faltam and escrever:
        kw("project.project", "write", [[TEMPLATE_ID], faltam], allow_write=True)
        v = kw("project.project", "read", [[TEMPLATE_ID],
               ["allow_milestones", "allow_task_dependencies"]])[0]
        print(f"  reconciliacao: {v}")

if __name__ == "__main__":
    main()
